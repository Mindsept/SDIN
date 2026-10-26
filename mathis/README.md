# Skills d'utilisation des services SDIN

Ces trois skills traduisent les usages des services en instructions utilisables
par un agent. La présentation d'origine, `sdin-skills-services.html`, n'est pas
incluse dans ce dépôt. Le service est déjà retenu : ces dossiers
cadrent son utilisation, sans intégrer l'arbitrage entre services.

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
Les assets sont des exemples : les copier dans l'app avant adaptation, sans y
inscrire de secrets. Les seuils et durées laissés à définir viennent du besoin
de l'app ; ils ne constituent pas des KPI imposés pour choisir une architecture.

Les dossiers sont versionnés dans le TD ; ils ne sont pas installés dans le profil
global de l'agent. Pour les utiliser depuis ce dépôt, demander par exemple :
« Applique le skill `mathis/sdin-umami-instrumentation/SKILL.md` à mon app. »
Une fois installé dans un emplacement reconnu par l'agent, son nom `$sdin-umami-instrumentation`
permet également de l'invoquer.

## État de livraison

Instructions, références et modèles disponibles. Les scénarios décrits sont des
protocoles à exécuter sur les applications ; ils ne constituent pas des résultats
de tests runtime. La création de ces dossiers ne provisionne aucun service.
