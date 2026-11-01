# Skills d'utilisation des services SDIN

Ces trois skills cadrent l'analytics, les logs et la livraison d'images pour un
agent. Le support historique `presentations/sdin-skills-services.html` mentionné
à leur création est absent de cette branche : utiliser les contrats locaux et
sources techniques vérifiables des références. Réutiliser le service déjà retenu ; en
l'absence de choix, vérifier brièvement le besoin avant d'ajouter une intégration.
Un diagnostic ponctuel, un événement analytics ou une inspection d'image ne demande
pas le même livrable qu'une instrumentation complète ou une publication.

| Skill | Point d'entrée | Livrables principaux |
|---|---|---|
| Umami | [SKILL.md](sdin-umami-instrumentation/SKILL.md) | Plan de tracking, instrumentation minimale, preuves du parcours |
| Dozzle | [SKILL.md](sdin-dozzle-diagnostic/SKILL.md) | Contrat de logs, diagnostic corrélé, politique de volume |
| Registry | [SKILL.md](sdin-registry-delivery/SKILL.md) | Entrées de build, références publiées, rétention et rollback |

## Organisation d'un dossier

- `SKILL.md` : déclenchement, entrées, démarche et contraintes essentielles.
- `agents/openai.yaml` : nom et description destinés à l'interface de l'agent.
- `references/patterns.md` : adaptation des pratiques classiques aux besoins et contraintes.
- `references/integration.md` : détails du socle et procédures applicables.
- `references/validation.md` : scénarios de vérification et preuves à produire.
- `assets/` : modèles ou exemples à copier et adapter dans l'application.

Lire le point d'entrée, puis uniquement les références nécessaires à la tâche.
Les assets sont des exemples : compléter d'abord l'existant et ne copier que les
éléments utiles, sans secrets. Les seuils et durées laissés à définir viennent du besoin
de l'app ; ils ne constituent pas des KPI imposés pour choisir une architecture.

Les dossiers sont versionnés dans le TD ; ils ne sont pas installés dans le profil
global de l'agent. Pour les utiliser depuis ce dépôt, demander par exemple :
« Applique le skill `Skills/sdin-umami-instrumentation/SKILL.md` à mon app. »
Une fois installé dans un emplacement reconnu par l'agent, son nom `$sdin-umami-instrumentation`
permet également de l'invoquer.

## État de livraison

Instructions, références et modèles disponibles. Les scénarios décrits sont des
protocoles à exécuter sur les applications ; ils ne constituent pas des résultats
de tests runtime. La création de ces dossiers ne provisionne aucun service.
