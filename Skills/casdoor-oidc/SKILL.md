---
name: casdoor-oidc
description: "Concevoir, implémenter ou revoir la connexion et les droits métier des applications du TD avec Casdoor/OIDC : client par app, Authorization Code avec PKCE, validation des tokens, sessions serveur, autorisation et personas e2e. Utiliser lorsqu'une app a besoin d'identifier ses utilisateurs ou protéger leurs ressources. Ne pas imposer de login à une app publique sans besoin ni utiliser Casdoor comme store de secrets ou gateway IA."
---

# Casdoor : connexion OIDC et accès métier

Partir du prompt utilisateur : qui utilise l'app, quelles ressources doivent
être privées et quelles actions chaque persona peut effectuer ? Ne pas imposer
un document pour stocker le prompt ni ajouter des comptes à un produit qui n'en
a pas besoin. Définir d'abord les besoins d'identité et d'autorisation.

## Lectures ciblées

- Toute intégration : [contrat de la plateforme et limites](references/platform-contract.md).
- Code et choix du flux : [patterns et exemples](references/integration-patterns.md).
- Explication des règles : [justification](references/design-rationale.md).
- Exemples de contrôles métier après OIDC : [assets/auth-policy.ts](assets/auth-policy.ts).

Lire les scripts locaux avant de les modifier. Utiliser une bibliothèque OIDC
maintenue, comme `openid-client` dans les snippets, et vérifier l'API de la
version verrouillée. Les assets ne sont pas un moteur JWT ou un validateur OIDC.

## Règles du harnais

`MUST` désigne une exigence proposée ; `SHOULD` une préférence justifiable.
Ne pas confondre une règle avec une garantie déjà imposée par le TD.

| ID | Niveau | Instruction |
|---|---|---|
| IDP-01 | MUST | Utiliser Casdoor pour la connexion des utilisateurs quand le besoin existe. Ne pas ajouter une base de mots de passe locale ou un endpoint de faux login. Les profils/données métier peuvent rester dans la base app, liés à l'identité vérifiée `(iss, sub)`. |
| IDP-02 | MUST | Utiliser un client OIDC propre à l'app, provisionné par les scripts. Charger `secret/<app>/oidc` côté serveur via OpenBao. Ne jamais utiliser `secret/core/idp`, le compte admin ou le client bootstrap dans le runtime métier. |
| IDP-03 | SHOULD | Pour une app web avec backend, choisir Authorization Code + PKCE S256 dans le backend et une session opaque côté navigateur. Une SPA/native sans backend peut nécessiter un client public PKCE, à provisionner explicitement ; jamais de client secret dans le frontend. |
| IDP-04 | MUST | Lier chaque tentative au navigateur initiateur avec une transaction courte à usage unique : state, nonce, verifier PKCE et callback exact. Consommer atomiquement la transaction, refuser l'expiration, les répétitions et les doublons de paramètres. Aucun implicit/password grant dans le login métier. |
| IDP-05 | MUST | Vérifier via la bibliothèque la réponse OIDC : issuer exact, audience/client, dates, nonce et signature avec JWKS/algorithmes approuvés. Ne pas accepter un JWT simplement décodé ni désactiver ces contrôles pour contourner le mélange d'URLs internes/publiques. |
| IDP-06 | MUST | Distinguer ID token (connexion), access token (ressource), refresh token, cookie de session et credentials workload. Ne pas utiliser un ID token comme bearer générique pour les API, une vkey APISIX comme session ou un client_credentials comme identité utilisateur. |
| IDP-07 | MUST | Garder tokens et client secret côté serveur pour le pattern backend. Cookie de session HttpOnly, Secure en HTTPS, SameSite adapté ; ID frais après login et droits sensibles. Protéger les mutations par CSRF et origine exacte, et limiter CORS aux origines nécessaires. |
| IDP-08 | MUST | Autoriser chaque action côté serveur et filtrer chaque ressource/tenant. Déduire les rôles uniquement de claims vérifiés ou d'une source serveur fiable, avec mapping explicite des groupes de l'app. Ne pas accepter `role`, `owner`, `tenant` ou `isAdmin` du navigateur comme preuve. |
| IDP-09 | MUST | Fixer les URLs de confiance en configuration serveur : issuer, endpoints et callback. Pas de wildcard de redirect ni de retour externe libre. Ne pas construire ces URLs depuis Host/X-Forwarded-* non validés ni accepter un JWKS fourni par un token. |
| IDP-10 | MUST | Définir expiration, logout local, éventuel SSO logout et invalidation des droits. Pas de session éternelle ni de refresh inventé : vérifier le grant et le support réels. Refuser les nouveaux logins si l'IdP est indisponible ; définir la validité des sessions existantes. |
| IDP-11 | MUST | Tester avec les personas métier via `seed-test-users.sh`, sans bypass ni utilisateur admin de plateforme. Les passwords partagés sont réservés au dev ; l'outil e2e lit son secret, le runtime ne le distribue pas et le README versionné n'en publie pas les valeurs. |
| IDP-12 | MUST | Vérifier login, replay, mauvais issuer/audience/nonce, CSRF, droits insuffisants et accès inter-utilisateur/tenant. Ne pas logger tokens, codes, secrets ou URL complète du callback. Les tests d'assets prouvent les guards, pas la cryptographie ni le flux Casdoor live. |

## Architecture attendue pour une app web

```text
Navigateur → /auth/login → Casdoor → /auth/callback (backend)
                                    ↓ validation OIDC
                              session serveur fraîche
Navigateur + cookie → API → autorisation métier → ressource
OpenBao → client OIDC du backend
```

Une même origine frontend/API via reverse proxy simplifie cookies et CORS ; ce
pattern reste un choix de déploiement à adapter aux ports du TD. Le SSO ne
remplace pas les règles d'accès de l'app. Ne pas imposer un worker, un moteur de
policy ou un store de sessions supplémentaire si l'app dispose déjà de ce qui
est nécessaire.

## Livraison attendue

Expliquer le flux retenu, le client/callback, les personas et droits par ressource,
les sessions et leur expiration, les tests et les limites de développement.
Ne pas changer l'IdP partagé, ses clés ou tous ses clients pour faire passer une
seule app. Préparer les évolutions nécessaires dans le périmètre demandé.
