# Casdoor : contrat local et points à vérifier

Inspection du dépôt SDIN le 14 octobre 2026. Sources depuis sa racine :
`td/core-platform/podman-compose.yml`, `idp/seed-and-deploy.sh`,
`idp/onboard-oidc.sh`, `idp/seed-test-users.sh` sous `td/core-platform/`.

## Service et provisioning

Image `docker.io/casbin/casdoor:v1.858.0`, conteneur `casdoor.internal`, aliases
`casdoor.internal` et `idp.internal`. UI hôte `http://localhost:9300`, service
interne `http://idp.internal:8000`. Persistence dans le PostgreSQL partagé.

Le seed crée la base/utilisateur Casdoor, redéploie l'IdP, rotate le compte
administrateur initial et publie `secret/core/idp` avec les credentials d'un
client de provisioning `platform-bootstrap`. Ces credentials sont privilégiés,
réservés aux scripts : ne pas les lire depuis le backend métier.

Depuis `td/core-platform/`, après le démarrage des seeds :

```bash
./idp/onboard-oidc.sh mon-app http://localhost:8001/auth/callback
./idp/seed-test-users.sh mon-app lecteur redacteur
```

Le callback est une URL publique exacte du backend, adaptée au bloc de ports de
l'app ; `8001` illustre le bloc par défaut. Choisir les personas du besoin réel.

`onboard-oidc.sh` crée une application possédée par `admin`, dans l'organisation
`built-in`, avec `authorization_code`. L'identifiant administratif est
`admin/<app>`, pas `built-in/<app>`. Relancer le script remplace la liste de
redirect URIs par le callback donné ; il ne l'ajoute pas à plusieurs environnements.
Son update lit le record complet pour ne pas effacer ses autres champs.

## Secret runtime de l'app

`secret/<app>/oidc` contient :

| Champ | Valeur construite par le script |
|---|---|
| `issuer` | URL interne, par défaut `http://idp.internal:8000` |
| `public_issuer` | URL publique/hôte, par défaut `http://localhost:9300` |
| `client_id`, `client_secret` | Credentials de l'app, jamais du client bootstrap |
| `authorize_endpoint` | URL publique + `/login/oauth/authorize` |
| `token_endpoint` | URL publique + `/api/login/oauth/access_token` |
| `userinfo_endpoint` | URL publique + `/api/userinfo` |
| `jwks_uri` | URL publique + `/.well-known/jwks` |
| `redirect_uri` | Callback fourni à l'onboarding |

Ce tableau décrit le script, pas une discovery validée. L'issuer d'identité
doit correspondre exactement à la discovery et au `iss` des tokens réellement
émis. Un alias réseau interne n'est pas automatiquement le bon issuer.

## Frontière réseau interne/public : vérifier avant de coder le login

Le navigateur doit joindre l'autorization endpoint public. Le backend doit
joindre token endpoint, discovery et JWKS. Dans un conteneur, `localhost:9300`
désigne ce conteneur : les URLs publiées par le script peuvent donc être
inaccessibles depuis l'API. Le champ `issuer` interne peut aussi diverger de
l'issuer public annoncé/émis.

Privilégier une URL canonique stable accessible aux deux côtés, avec DNS/reverse
proxy configuré pour le déploiement. Si un transport interne différent est
nécessaire, le configurer explicitement pour des endpoints approuvés en gardant
l'issuer d'identité intact et tester la bibliothèque choisie. Ne pas remplacer
aveuglément les URLs ni modifier `iss` ou désactiver sa validation.

La [documentation OIDC Casdoor actuelle](https://casdoor.ai/docs/how-to-connect/oidc-client/)
décrit aussi des variantes par application. Elle peut être plus récente que
v1.858.0. Le TD construit des endpoints globaux ; ne pas inventer un issuer
par app à partir d'une autre version. Inspecter la discovery réelle et le format
de token du client provisionné avant de choisir JWKS/algorithmes et claims.

## Identités de test et groupes

Le seed crée `<app>-test-<persona>` et un groupe `<app>-<persona>` dans `built-in`.
Les records de groupes utilisent la forme `built-in/<app>-<persona>`.
Le secret `secret/<app>/test-users` contient `shared_password` et les champs
`<persona>_username`. Le mot de passe commun est une facilité de dev.

Ne pas supposer que l'ID token ou UserInfo contient ces groupes sous un champ
précis. Vérifier les claims réellement délivrés/scopes et leur format ; sinon
utiliser un mapping de permissions dans la base app à partir de `(iss, sub)`.
Ne pas appeler l'API admin avec le bootstrap pour chaque requête métier.

Le script réapplique les mots de passe mais réutilise les utilisateurs existants
sans resynchroniser automatiquement leurs groupes. Il ne supprime pas les
anciennes personas. Plusieurs réponses admin sont jugées sur JSON `status`,
mais certains add-group/add-user sont seulement redirigés : relire l'état et
tester le login et les droits plutôt que croire le message « created ».

## Simplifications et écarts

- HTTP, single-instance, compte admin/passwords de démo, token OpenBao root et
  absence de MFA imposée : cette configuration ne constitue pas une cible prod.
- L'onboarding ne configure pas explicitement toute la policy de tokens :
  algorithme/certificat, scopes, refresh, logout et groupes doivent être vérifiés.
- Un grant `authorization_code` autorisé ne prouve pas que PKCE S256 est exigé
  côté serveur. L'app l'utilise et un test vérifie qu'un mauvais verifier échoue.
- Le seed gère la rotation administrative initiale ; relancer avec une nouvelle
  variable n'est pas une procédure générique de rotation du client app.
- Le store OpenBao est volatile alors que la base Casdoor persiste. Après sa
  perte, réinitialiser/reconcilier le provisioning ; ne pas ouvrir un bypass.
- Le script demande de documenter le password commun dans le README. Le harnais
  garde le README sans valeur secrète et fournit la procédure locale d'accès
  aux credentials e2e ; il ne modifie pas le script de plateforme à lui seul.

## Sources complémentaires

- [OAuth/PKCE Casdoor](https://casdoor.ai/docs/how-to-connect/oauth/)
- [OIDC Core : validation](https://openid.net/specs/openid-connect-core-1_0.html)
- [OAuth Security BCP, RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)

Les docs établissent les patterns de protocole ; les tests d'intégration restent
nécessaires pour le contrat effectif de cette image et de chaque application.
