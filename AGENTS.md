# Navigation dans le projet SDIN

Ce fichier oriente vers les contributions existantes. Il n'ajoute pas de doctrine
d'architecture, ne remplace aucun skill et n'installe rien dans le profil de l'agent.

## Contexte et sources

- Le dépôt fournit un socle partagé et des guides pour les applications qui le
  consomment ; ne pas supposer qu'une application métier existe déjà.
- Partir de la demande, des instructions de l'application cible et du code
  existant. Conserver les réponses et décisions déjà établies.
- Pour un fait de plateforme, consulter les fichiers réels sous
  [td/core-platform](td/core-platform/README.md), notamment le Compose, les
  scripts et templates pertinents. Distinguer configuration déclarée et état réel.
- Consulter les [règles CCoE](Elyes/CCOE-RULES.md) et leur
  [matrice d'audit](Elyes/audit-matrix.yml) selon leur périmètre ; ne pas étendre
  leurs exigences à un service non retenu ou à une autorité qu'elles ne revendiquent pas.

## Choisir le point d'entrée

| Tâche | Route |
|---|---|
| Nouvelle application, refonte, choix de stack ou organisation du code | [archi](skills/archi/SKILL.md) ; suivre sa table de routage, puis devops-and-choice pour les choix de services utiles |
| Comparaison de services, combinaisons, CI/CD ou exploitation | [devops-and-choice](skills/devops_and_choice/SKILL.md) ; suivre ses références et relais spécialisés |
| Intégration PostgreSQL, S3 ou Valkey déjà retenue | [PostgreSQL](Elyes/postgresql/SKILL.md), [SeaweedFS/S3](Elyes/seaweedfs-s3/SKILL.md) ou [Valkey](Elyes/valkey/SKILL.md), selon le changement |
| Intégration d'identité, de secrets ou d'appels IA | [Casdoor](leandro/casdoor-oidc/SKILL.md), [OpenBao](leandro/openbao-secrets/SKILL.md) ou [APISIX](leandro/apisix-llm/SKILL.md) |
| Concevoir ou modifier un processus durable | [Temporal workflows](hugo/temporal-workflows/SKILL.md) |
| Examiner une exécution Temporal existante | [Temporal operations](hugo/temporal-operations/SKILL.md) |
| Instrumenter les usages, structurer/diagnostiquer les logs ou livrer des images | [Umami](mathis/sdin-umami-instrumentation/SKILL.md), [Dozzle](mathis/sdin-dozzle-diagnostic/SKILL.md) ou [Registry](mathis/sdin-registry-delivery/SKILL.md) |
| Petite correction dans une application existante | Lire les fichiers concernés et le skill utile ; ne pas reprendre un cadrage complet sans changement qui le justifie |

## Suivre la route choisie

Lire le SKILL.md retenu puis seulement les références nécessaires. Ses règles,
conditions d'application, exemples et limites restent la source détaillée.
Transmettre les faits connus et la question restante lors d'un relais entre
skills ; ne pas recommencer les questionnaires ni boucler entre points d'entrée.

Pour un livrable, utiliser les modèles indiqués par le skill. Pour un JSON
d'architecture, suivre le [contrat et ses limites](skills/archi/references/contrat-machine.md).
La [cartographie](docs/architecture/index.html) et la
[présentation](presentations/sdi-2026.src.html) apportent le contexte.

Distinguer proposition, inspection, contrôle local et test sur la plateforme.
Vérifier l'existence des scripts cités avant exécution : les références GitHub
Actions/lifecycle des skills transverses ne correspondent pas encore toutes à
des fichiers livrés. Lire le cycle de vie réel dans le README du socle.
Une demande d'analyse seule ne déclenche pas de provisioning ou de déploiement.
