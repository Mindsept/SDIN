---
name: openbao-secrets
description: "Concevoir, implémenter ou revoir les secrets des applications du TD avec OpenBao : lecture KV v2 côté serveur, séparation provisioning/runtime, politiques minimales, rotation et audit. Utiliser pour les credentials PostgreSQL, S3, APISIX, OIDC ou d'intégrations métier. Ne pas utiliser OpenBao comme base métier, magasin de sessions ou fournisseur de connexion des utilisateurs."
---

# OpenBao : secrets applicatifs et accès minimaux

Partir du prompt utilisateur et des services réellement nécessaires. Ne pas
imposer un document pour stocker la demande. Identifier les secrets de chaque
processus, leur propriétaire, leur source, leur mode de chargement et leur cycle
de vie avant d'ajouter une intégration.

## Minimum utile

Une app statique sans secret serveur n'ajoute ni lecteur OpenBao ni backend pour
en avoir un. Réutiliser les secrets et le loader des seuls services retenus :
un client chargé au démarrage est le point de départ, pas un sidecar ou une lecture
par requête. Réduire la policy d'exemple aux chemins réellement consommés.

Partir des credentials KV statiques déjà provisionnés. Ajouter secrets dynamiques,
renouvellement automatique ou agent dédié seulement quand la rotation/lease ou le
mode de déploiement l'exige et que le mécanisme est réellement configuré. Ces ajouts
ne remplacent jamais une identité runtime à droits limités hors de l'exception de dev.

Dimensionner délai et nombre d'essais de chargement selon le budget de démarrage ;
choisir un refresh seulement si la rotation l'exige, avec concurrence bornée et
sans boucle rapide en cas de panne. Après le démarrage, distinguer store indisponible
et credentials déjà chargés encore valides : ne pas arrêter tous les parcours si
leurs clients fonctionnent. Aucune prolongation implicite d'une lease expirée.

## Références à consulter selon le travail

- Toute intégration : [contrat local et limites](references/platform-contract.md).
- Implémentation/provisioning : [patterns et snippets](references/integration-patterns.md).
- Discussion des décisions : [justification des règles](references/design-rationale.md).
- Exemple de lecteur KV v2 serveur : [assets/secret-reader.ts](assets/secret-reader.ts).
- Exemple de politique pour une API : [assets/app-runtime-policy.hcl](assets/app-runtime-policy.hcl).

Vérifier les sources `td/core-platform/` indiquées dans le contrat avant de
modifier un bootstrap. Réutiliser un lecteur de secrets existant ; ne pas en
empiler un second à côté de celui déjà livré par une autre skill.

## Règles du harnais

Les `MUST` sont les exigences proposées pour les apps ; les `SHOULD` sont des
préférences à adapter avec une justification. Les politiques et identités de
production ci-dessous ne sont pas déjà provisionnées par le TD.

| ID | Niveau | Instruction |
|---|---|---|
| BAO-01 | MUST | Utiliser OpenBao pour les secrets partagés de l'app ; garder les données métier dans PostgreSQL/S3 et les sessions dans le store de l'app. Ne pas créer de secret sans dépendance qui l'exige. Les paramètres publics peuvent rester dans la configuration normale. |
| BAO-02 | MUST | Séparer provisioning et runtime. Le bootstrap peut créer les ressources autorisées ; le serveur de l'app ne fait que lire ses secrets nécessaires. Ne pas embarquer de droits d'administration de plateforme dans la logique métier. |
| BAO-03 | MUST | Définir les accès par app et par processus sur des chemins précis. Ne pas lire `secret/core/*`, les secrets d'autres apps ou `test-users` depuis l'API de production. Un préfixe de chemin ne prouve pas l'isolation si le token est root. |
| BAO-04 | MUST | Garder tokens et valeurs côté serveur : jamais dans un bundle, un `VITE_*`, une URL, une réponse HTTP, un log, une fixture réelle ou un document versionné. `.env.example` décrit les noms sans valeurs. Une valeur committée doit être révoquée/rotatée, pas seulement supprimée. |
| BAO-05 | SHOULD | Charger et valider les secrets au démarrage ou au refresh contrôlé ; injecter les dépendances déjà configurées dans les handlers. Ne pas interroger OpenBao pour chaque requête métier. Prévoir le rechargement lors d'une rotation. |
| BAO-06 | MUST | Distinguer 403, 404, indisponibilité et secret mal formé. Ne pas remplacer un échec de lecture par un mot de passe par défaut, une clé nouvelle ou une réécriture. La readiness dépend des fonctionnalités indispensables, pas d'une impression de disponibilité. |
| BAO-07 | MUST | Respecter KV v2 : chemins HTTP/policies `secret/data/...`, enveloppe `data.data`, versions, CAS pour les écritures concurrentes. Ne pas transformer tout échec de `patch` en `put` d'une map partagée. |
| BAO-08 | MUST | Décrire l'amorçage de l'identité du workload. Le token root public est une exception locale du TD ; hors dev, utiliser une identité limitée et un moyen de livraison adapté. Ne pas stocker dans OpenBao le seul credential permettant d'y accéder. |
| BAO-09 | MUST | Faire une rotation coordonnée entre service cible, secret et clients ; vérifier les nouveaux credentials puis révoquer les anciens. Une mise à jour KV ou un rollback de version ne change pas à elle seule le mot de passe du service cible. |
| BAO-10 | MUST | Distinguer secret statique KV, token d'accès et secret dynamique sous lease. Renouveler seulement ce qui est renouvelable ; ne pas inventer un moteur de credentials dynamiques ou AppRole déjà actif. |
| BAO-11 | MUST | Conserver l'audit déclaratif fourni et diagnostiquer sans afficher les valeurs. Les HMAC protègent certains champs, pas tous les métadonnées. Ne pas désactiver l'audit pour faire passer une opération. |
| BAO-12 | MUST | Tester les accès refusés, la configuration absente, la rotation et les erreurs. Des tests du lecteur ne prouvent pas les ACL : vérifier les policies avec un token réellement limité dans un environnement adapté. |

## Répartition des responsabilités

```text
Provisioning autorisé → ressource cible + secret OpenBao
Identité workload → token limité → lecture KV → client DB/S3/OIDC/LLM
Requête utilisateur → handler → client déjà configuré
```

La skill APISIX traite la vkey et interdit les clés fournisseur dans l'app.
La skill Casdoor traite le client OIDC ; le token OpenBao ne devient jamais une
session utilisateur. Ne pas déplacer les secrets vers Casdoor ou le frontend
pour résoudre une panne du store.

## Livraison attendue

Présenter les chemins nécessaires sans valeurs, les droits de chaque processus,
le chargement/refresh, la rotation, les tests et les limites de dev restantes.
Adapter les snippets au produit et à l'environnement ; une proposition de policy
ne l'applique pas et ne donne pas permission de changer une plateforme partagée.
