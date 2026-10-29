# Skills SDIN

Les 13 skills du dépôt sont regroupés dans ce dossier. Chaque sous-dossier conserve son `SKILL.md` et ses propres ressources (`references/`, `assets/`, `agents/`, `scripts/`). Les liens entre skills utilisent désormais leur emplacement sous `Skills/`.

Partir du besoin et réutiliser les décisions existantes. Un service disponible n'est
pas obligatoire ; les exemples et modèles ne sont à copier que s'ils comblent un
besoin réel. Dimensionner limites, concurrence et rétention avant d'ajouter des
composants, sans retirer les garanties de sécurité et de cohérence.

Pour les itérations : [scénarios de revue et vérifications locales](validation.md).

## Contributions regroupées

| Contribution d'origine | Skills |
|---|---|
| Elyes | [`postgresql`](postgresql/SKILL.md), [`seaweedfs-s3`](seaweedfs-s3/SKILL.md), [`valkey`](valkey/SKILL.md) |
| Hugo | [`temporal-workflows`](temporal-workflows/SKILL.md), [`temporal-operations`](temporal-operations/SKILL.md) |
| Léandro | [`apisix-llm`](apisix-llm/SKILL.md), [`casdoor-oidc`](casdoor-oidc/SKILL.md), [`openbao-secrets`](openbao-secrets/SKILL.md) |
| Mathis | [`sdin-umami-instrumentation`](sdin-umami-instrumentation/SKILL.md), [`sdin-dozzle-diagnostic`](sdin-dozzle-diagnostic/SKILL.md), [`sdin-registry-delivery`](sdin-registry-delivery/SKILL.md) |
| Dossier commun `skills/` | [`archi`](archi/SKILL.md), [`devops_and_choice`](devops_and_choice/SKILL.md) |

Les deux derniers étaient dans le dossier commun `skills/`, sans attribution nominative dans l'arborescence source. Aucun dossier `hamza/` n'existait dans le dépôt cloné.

Pour le catalogue principal et les autres ressources, voir le [README du dépôt](../README.md).

Le [guide des contributions de Mathis](README-Mathis.md) conserve les instructions, le contexte et les précautions du README d’origine.

Les [règles CCOE](CCOE-RULES.md), la [matrice d’audit](audit-matrix.yml) et le [guide des contributions d’Elyes](README-Elyes.md) sont également regroupés ici.
