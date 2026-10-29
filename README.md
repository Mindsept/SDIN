# SDIN — guider une IA sur la plateforme

Ce dépôt rassemble un socle de plateforme partagé, ses scripts et templates,
et les contributions destinées à aider une IA à développer une application
qui le consomme. Il ne contient pas d'application métier complète.

Ce README et [AGENTS.md](AGENTS.md) servent de points d'entrée :
ils orientent vers le travail existant sans remplacer ses règles ni ses références.

## Commencer

1. Fournir le besoin et l'emplacement de l'application concernée à l'agent.
2. Lui demander de lire [AGENTS.md](AGENTS.md), puis de suivre la route adaptée.
3. Utiliser les skills spécialisés uniquement pour les services concernés.

Exemple de demande :

> Lis AGENTS.md à la racine du dépôt SDIN. À partir de mon besoin et de mon
> application existante, suis les skills pertinents, conserve les décisions déjà
> établies et distingue les choix proposés des vérifications réellement exécutées.

Les skills sont des dossiers versionnés. Ce README ne les installe pas dans le
profil de l'agent. Si ses instructions ne sont pas chargées automatiquement,
indiquer explicitement le chemin d'AGENTS.md dans le dépôt.

Tous les skills sont regroupés dans [Skills/](Skills/). Le
[catalogue](Skills/README.md) présente leur organisation et leurs ressources.

## Les contributions à consulter selon le besoin

| Besoin | Point d'entrée existant |
|---|---|
| Cadrage, architecture, langages/frameworks, structure du code, ORM et objectifs de temps de réponse | [archi](Skills/archi/SKILL.md) |
| Choix et combinaisons de services, livraison et exploitation | [devops-and-choice](Skills/devops_and_choice/SKILL.md) |
| Persistance, fichiers et état temporaire partagé | [PostgreSQL](Skills/postgresql/SKILL.md), [SeaweedFS/S3](Skills/seaweedfs-s3/SKILL.md), [Valkey](Skills/valkey/SKILL.md) |
| Identité, secrets et appels IA | [Casdoor/OIDC](Skills/casdoor-oidc/SKILL.md), [OpenBao](Skills/openbao-secrets/SKILL.md), [APISIX](Skills/apisix-llm/SKILL.md) |
| Processus durables et diagnostic d'exécutions | [Temporal workflows](Skills/temporal-workflows/SKILL.md), [Temporal operations](Skills/temporal-operations/SKILL.md) |
| Mesure des usages, logs et livraison d'images | [Umami](Skills/sdin-umami-instrumentation/SKILL.md), [Dozzle](Skills/sdin-dozzle-diagnostic/SKILL.md), [Registry](Skills/sdin-registry-delivery/SKILL.md) |

Le catalogue contient 13 skills : 2 transverses et 11 spécialisés.
Les tables de routage internes d'archi et devops-and-choice précisent les
références à charger et les relais entre contributions.

## Sources et outils déjà produits

- [Socle et contrats](td/core-platform/README.md),
  [configuration Compose](td/core-platform/podman-compose.yml) et
  [prérequis](td/core-platform/requirements.md) : configuration et fonctionnement du socle.
- [Règles CCoE](Skills/CCOE-RULES.md) et [matrice d'audit](Skills/audit-matrix.yml) :
  doctrine locale, périmètres d'application et modes de revue.
- [Contributions Elyes](Skills/README-Elyes.md) et [Mathis](Skills/README-Mathis.md) :
  organisation et limites de leurs livrables.
- [Contrat JSON d'architecture](Skills/archi/references/contrat-machine.md),
  [validateur](Skills/archi/scripts/validate_architecture.py) et
  [tests du validateur](Skills/archi/scripts/test_validate_architecture.py) :
  vérification des déclarations, dans les limites décrites par le contrat.
- [Modèles de décision d'architecture](Skills/archi/assets/decision-architecture.md),
  [plan de services](Skills/devops_and_choice/assets/service-plan.md),
  [runbook](Skills/devops_and_choice/assets/operations-runbook.md) et
  [README applicatif](td/core-platform/templates/README.app.md) :
  livrables à adapter selon la tâche.
- [Cartographie et parcours illustratifs](docs/architecture/index.html) et
  [présentation du cours](presentations/sdi-2026.src.html) : contexte et explications.

Les références, exemples de code et scénarios de validation propres à chaque
service restent dans son dossier. Les consulter depuis son SKILL.md.

## État de la livraison

Les instructions, scripts du socle, templates et contrôles locaux sont présents.
Un scénario décrit ou un fichier de configuration ne prouve pas qu'un test
d'intégration ou un déploiement a réussi.

Le cycle de vie utilise les mêmes scripts locaux et GitHub Actions :
[contrôles du dépôt](.github/workflows/checks.yml),
[opérations manuelles du socle](.github/workflows/core-platform.yml),
[modèle applicatif](td/core-platform/templates/github-actions.yml).
Le [guide de migration et de configuration](docs/github-migration.md) précise
les équivalences avec les anciens pipelines et les réglages GitHub à effectuer.
