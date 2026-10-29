# OpenBao : contrat de la plateforme

Inspection du dépôt SDIN le 14 octobre 2026. Sources de vérité depuis sa racine :
`td/core-platform/podman-compose.yml`, `lib/secrets.sh`, `openbao/audit.hcl`,
`audit-trail.sh` et `templates/bootstrap.sh` sous `td/core-platform/`.

## Coordonnées et données

- Image : `docker.io/openbao/openbao:2.6`, mode dev, secrets en mémoire.
- Conteneur : `openbao.internal` ; alias réseau compatible : `vault.internal`.
- API interne : `http://openbao.internal:8200` ; hôte : `http://localhost:8200`.
- Le template d'app injecte `VAULT_ADDR`, `VAULT_TOKEN` et `VAULT_PATH`.
- Les scripts utilisent `BAO_*` avec compatibilité `VAULT_*`. Le résolveur teste
  un CLI hôte qui répond, sinon exécute `bao` dans le conteneur. `type -P` évite
  la récursion sur la fonction shell portant le même nom.

Le mount dev `secret` est KV v2 : une lecture logique de
`secret/mon-app/oidc` correspond à `GET /v1/secret/data/mon-app/oidc`.
Le corps renvoie les valeurs sous `data.data` et la version sous `data.metadata`.
[Contrat KV v2](https://openbao.org/docs/secrets/kv/kv-v2/).

| Chemin logique | Propriétaire / lecteurs attendus |
|---|---|
| `secret/<app>/postgres` | Bootstrap app ; API/worker utilisant sa base |
| `secret/<app>/objectstore` | Bootstrap app ; processus utilisant son bucket |
| `secret/<app>/llm` | Onboarding/option bootstrap ; backends IA |
| `secret/<app>/oidc` | Onboarding Casdoor ; backend de connexion |
| `secret/<app>/test-users` | Seed de personas ; outil e2e de dev uniquement |
| `secret/<app>/analytics` | Provisioning analytics ; processus pertinent |
| `secret/core/*` | Provisioning des services partagés ; pas le runtime métier |

Ne pas demander automatiquement tous ces chemins pour chaque application.
La vkey APISIX et le `client_secret` OIDC sont des secrets ; un `client_id`, un
port ou le nom d'une base ne le sont généralement pas à eux seuls.

## Garanties absentes ou limitées

1. Le token `root-dev-token` du Compose est public et privilégié. Les préfixes
   `<app>` ne constituent pas une frontière ACL avec ce token. Des policies
   minimales et une identité runtime restent à configurer pour une isolation.
2. Secrets en mémoire : redémarrer OpenBao les perd, même sans purge des volumes.
   Le volume `openbao-logs` conserve l'audit, pas les secrets KV.
3. HTTP et credentials de démonstration : aucune garantie de chiffrement du
   transport ou de protection du bootstrap de production.
4. Les mots de passe PostgreSQL/S3/OIDC sont stockés comme valeurs KV statiques.
   Le dépôt ne configure pas de moteur database dynamique, AppRole ni renewal
   runtime. La disponibilité upstream de ces mécanismes ne les rend pas actifs.
5. `bao_put_map` tente `kv patch`, puis `kv put` sur n'importe quel échec. Un
   refus, un timeout ou un conflit ne prouvent pas l'absence du chemin. Ce helper
   n'est pas une garantie de mise à jour concurrente sûre d'une map partagée.
6. Le bootstrap réutilise la présence d'un secret comme indication de provisioning.
   Elle ne prouve pas que le compte cible, le bucket ou son mot de passe sont
   encore cohérents. Après perte du store, certains comptes persistants peuvent
   être recréés ou leur mot de passe remplacé : recharger les clients concernés.

## Audit et suppression

Le fichier `openbao/audit.hcl` déclare le device `file/`, monté par Compose.
Réutiliser `./audit-trail.sh` depuis `td/core-platform/` pour son état et les
métadonnées. Ne pas ajouter une commande d'activation d'audit copiée d'une autre
version : cette plateforme utilise le mode déclaratif prévu par son image.

Un audit contient des chemins et identifiants sensibles même si les valeurs sont
HMACées. L'accès et la rétention des logs doivent être contrôlés.
[Audit OpenBao](https://openbao.org/docs/audit/).

KV v2 distingue suppression logique d'une version, destruction de ses valeurs
et suppression des métadonnées/historique. Ne pas promettre l'effacement complet
avec un simple `kv delete`. Une purge des secrets ne révoque pas les credentials
encore acceptés par PostgreSQL, S3 ou un fournisseur externe.

## Évolutions à proposer si le déploiement l'exige

Store persistant, TLS, identités par workload, policies limitées, livraison
initiale du credential hors du store, TTL/renouvellement selon l'auth choisie,
backups et plan de rotation/reprise. AppRole est une option pour un workload
sans identité native adaptée, pas une obligation pour tous les environnements.
[AppRole](https://openbao.org/docs/auth/approle/),
[policies](https://openbao.org/docs/concepts/policies/).

Ces pages peuvent décrire une version plus récente que l'image 2.6 : valider
les opérations avancées contre l'image réelle avant de les adopter.
