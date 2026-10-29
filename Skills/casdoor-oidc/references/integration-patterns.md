# Patterns Casdoor et snippets OIDC

## Choix proportionné

| Besoin | Pattern |
|---|---|
| Site public sans données personnelles privées | Aucun login obligatoire |
| App web avec API et données privées | Backend OIDC + session serveur opaque |
| SPA/native sans backend confidentiel | Client public Authorization Code + PKCE, configuration distincte |
| Service-to-service | Identité machine et droits propres ; ne pas fabriquer un utilisateur |
| Documents ou données multi-tenant | Connexion + autorisation serveur par ressource et tenant |

Le pattern backend simplifie la confidentialité des tokens ; il nécessite
toujours protection CSRF, contrôle de session et autorisation. Garder les
données métier dans la base app avec une clé de liaison `(issuer, subject)`.

## Configurer une bibliothèque OIDC maintenue

Snippet pour l'API v6 de `openid-client`, à installer/verrouiller dans l'app si
elle n'a pas déjà une bibliothèque adaptée. Le snippet ne constitue pas un
serveur complet et n'a pas été exécuté contre l'IdP du TD.

```ts
import * as oidc from "openid-client";
import { safeReturnPath, assertCallbackLocation } from "./infrastructure/auth-policy.ts";

// secret/<app>/oidc lu au démarrage par le loader OpenBao du backend.
// canonicalIssuer est une configuration opérateur validée contre la discovery
// réelle, pas le champ issuer interne recopié sans vérification.
const config = await oidc.discovery(
  new URL(canonicalIssuer),
  settings.client_id,
  settings.client_secret,
  undefined,
  { execute: localDevelopment
    ? [oidc.allowInsecureRequests, oidc.enableNonRepudiationChecks]
    : [oidc.enableNonRepudiationChecks] },
);
// Avant tout login : valider les endpoints retournés contre une allowlist
// opérateur et vérifier l'algorithme signé approuvé pour le client réel.
```

`allowInsecureRequests` est réservé au dev local HTTP explicitement choisi.
Ne pas activer `NODE_TLS_REJECT_UNAUTHORIZED=0` ni désactiver la validation du
certificat. Le JWKS doit rester un endpoint de l'IdP approuvé, pas un `jku`
fourni dans un JWT non vérifié. `enableNonRepudiationChecks` demande la validation
JWS des réponses JWT ; garder aussi les contrôles d'issuer/audience/dates/nonce.
[API de signature](https://github.com/panva/openid-client/blob/main/docs/functions/enableNonRepudiationChecks.md),
[configuration HTTP locale](https://github.com/panva/openid-client/blob/main/docs/functions/allowInsecureRequests.md).

## Démarrer une transaction de login

Exemple de raccordement à un store serveur existant : `transactions` doit
conserver une entrée avec TTL et la consommer atomiquement, liée à un identifiant
aléatoire du navigateur stocké dans un cookie pré-auth protégé. Ne pas utiliser
une simple map non bornée en production ou un state global partagé.

```ts
async function startLogin(browserBinding: string, wantedReturnTo: string) {
  const state = oidc.randomState();
  const nonce = oidc.randomNonce();
  const verifier = oidc.randomPKCECodeVerifier();
  const challenge = await oidc.calculatePKCECodeChallenge(verifier);
  await transactions.put(state, {
    browserBinding, nonce, verifier,
    expiresAt: Date.now() + 5 * 60_000,
    returnTo: safeReturnPath(wantedReturnTo, ["/", "/documents"]),
  });
  return oidc.buildAuthorizationUrl(config, {
    redirect_uri: settings.redirect_uri,
    scope: "openid", // ajouter profile/email seulement si le produit en a besoin
    response_mode: "query",
    state, nonce,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });
}
```

Le backend redirige vers l'IdP. Les mots de passe sont saisis chez Casdoor, pas
dans un formulaire métier qui les transmettrait avec un password grant.
La cookie pré-auth doit être réellement liée au navigateur ; la connaissance
du state seul ne doit pas permettre de récupérer la transaction.

## Traiter le callback, puis créer une session fraîche

```ts
async function finishLogin(callbackUrl: URL, browserBinding: string) {
  assertCallbackLocation(callbackUrl, settings.redirect_uri);
  const state = callbackUrl.searchParams.get("state");
  if (!state) throw new Error("Connexion refusée");
  // takeBound vérifie le binding et retire atomiquement la transaction.
  const tx = await transactions.takeBound(state, browserBinding);
  if (!tx || tx.expiresAt <= Date.now()) throw new Error("Connexion refusée");
  const tokens = await oidc.authorizationCodeGrant(config, callbackUrl, {
    pkceCodeVerifier: tx.verifier,
    expectedState: state,
    expectedNonce: tx.nonce,
    idTokenExpected: true,
  });
  const claims = tokens.claims(); // après validation par la bibliothèque
  if (!claims) throw new Error("Connexion refusée");
  const identity = { issuer: claims.iss, subject: claims.sub };
  // Charger les permissions depuis une source serveur fiable pour cette identité.
  const permissions = await loadApplicationPermissions(identity);
  // Invalider/remplacer l'ancien ID, TTL idle + absolu ; ne pas retourner tokens.
  const session = await sessions.createFresh(browserBinding, identity, permissions);
  return { sessionId: session.id, returnTo: tx.returnTo };
}
```

Les noms `transactions`, `sessions`, `loadApplicationPermissions` désignent les
interfaces à implémenter avec les stores/middlewares de l'app ; ce n'est pas du
code à copier sans les contrats d'atomicité, expiration et rotation de session.
Le snippet traite un callback GET/query ; un `form_post` demande un raccordement
et une politique de cookies adaptés, sans supprimer state ou nonce.
[Contrôles de code grant](https://github.com/panva/openid-client/blob/main/docs/functions/authorizationCodeGrant.md).

Utiliser un algorithme signé convenu et validé pour le client : configurer la
métadonnée client `id_token_signed_response_alg` de la bibliothèque et les
certificats Casdoor conformément au contrat réel. Ne pas supposer `RS256` ou
inventer une clé à partir du secret client parce qu'un decode échoue.
Si UserInfo est utilisé, passer le `sub` attendu et vérifier sa correspondance.
Ne pas associer automatiquement deux comptes sur une adresse email non vérifiée.

## Cookies et mutations

Le navigateur conserve seulement un ID opaque. Cookie HttpOnly, Path `/`,
SameSite Lax pour ce flux query, Secure en HTTPS ; utiliser le préfixe `__Host-`
seulement avec ses conditions Secure et absence de Domain. Le HTTP du workshop
demande un cookie de dev distinct, jamais une désactivation implicite en prod.

Protéger les POST/PATCH/DELETE par le mécanisme CSRF du framework et un contrôle
d'origine exacte. Un bouton masqué et SameSite seul ne remplacent pas ce contrôle.
Ne pas faire d'action destructive en GET. Avec frontend/API sur des ports
différents, configurer une origine CORS précise et les credentials nécessaires,
sans wildcard. Le reverse proxy de même origine peut éviter cette configuration.

## Autorisation après authentification

Les assets contiennent un exemple pour des documents : mapping exact de groupes
vérifiés vers des rôles, tenant obligatoire et propriété du document. Adapter
ces règles aux personas réelles. Ne pas supposer qu'un groupe `admin` quelconque
fait de son membre un administrateur de cette app.

En SQL, filtrer la ressource dans la requête autorisée, par exemple tenant et
propriétaire, plutôt que charger tout le corpus et demander au frontend/LLM
de filtrer. Réappliquer les droits au worker avant un effet sensible et définir
ce qui se passe si les permissions ont changé depuis la création du job.

## Expiration, logout et tests

Définir TTL idle/absolu, invalidation et durée acceptable de permissions en cache.
Logout local = supprimer la session serveur et expirer son cookie ; logout SSO
demande un endpoint/protocole IdP vérifié. Les autres sessions et tokens ne sont
pas automatiquement révoqués par une suppression de cookie.

Le client provisionné n'active explicitement que `authorization_code` : ne pas
présumer qu'un refresh token/grant de renouvellement est disponible. Le demander
seulement si le produit l'exige et prévoir rotation/revocation et réauthentification.

```bash
# Depuis la racine du dépôt ; tests de guards, sans IdP ni credentials réels.
node --test Skills/casdoor-oidc/assets/auth-policy.test.ts
```

En intégration, tester le vrai flux avec les personas : verifier PKCE erroné,
issuer/audience/nonce erronés, callback rejoué, accès d'un autre utilisateur et
tenant, session expirée, logout et mutation sans CSRF. Ces scénarios ne sont
pas remplacés par les tests unitaires des assets.
