# Elyes — PostgreSQL, SeaweedFS/S3, Valkey

Les **3 skills** de cette contribution sont regroupés avec les autres skills dans ce dossier : un `SKILL.md` avec `name` et `description`, le contrat de la plateforme, le parcours de décision/implémentation, les preuves attendues et des références détaillées chargées au besoin.

- `postgresql/SKILL.md` : persistance relationnelle, migrations, droits utilisateurs et pgvector.
- `seaweedfs-s3/SKILL.md` : fichiers privés/publics, validation des uploads et dépôt initial du corpus RAG.
- `valkey/SKILL.md` : cache borné, Streams et jobs d'ingestion optionnels.

Chaque skill commence par décider si le service est utile. La non-utilisation est une décision valide, documentée dans « Structuring decisions » du README de l'application. Les sources canoniques de configuration sont dans `../td/core-platform/` : cette contribution ne modifie pas la plateforme commune et ne crée pas d'application métier.

Pour le RAG : déposer le document original dans S3 privé, extraire et découper son texte, vectoriser via `task:embed`, stocker chunks et embeddings dans PostgreSQL/pgvector, puis récupérer uniquement les passages autorisés. Valkey transporte des références de jobs seulement si une file est justifiée. Temporal couvre les workflows durables selon [`temporal-workflows`](temporal-workflows/SKILL.md) et [`temporal-operations`](temporal-operations/SKILL.md).

Chaque dossier de service est autonome et peut être copié dans le répertoire de skills de l'agent. `references/integration-patterns.md` apporte les détails. `CCOE-RULES.md` et `audit-matrix.yml` documentent la doctrine du TP et les modes de revue : ils ne constituent pas un contrôle automatique ni une preuve de sécurité de l'application.

Aucun test d'intégration avec les services n'est revendiqué pour cette contribution documentaire. Les critères dans les skills sont à vérifier lors de l'implémentation d'une application réelle.
