# Itérer sur les skills sans surdimensionner l'app

Ces scénarios servent à revoir le comportement des skills, pas à installer les
13 services. Pour une itération, prendre le point d'entrée concerné et les seuls
artefacts utiles du dépôt. Demander une réponse ou un changement local, sans
provisioning, publication ni appel payant implicite. Les résultats attendus sont
des critères de revue, pas la preuve de tests live déjà exécutés.

## Cas représentatifs

| Skill | Demande à essayer | Critère observable |
|---|---|---|
| archi | Une petite page de calcul publique, sans données à conserver | Pas de backend/services ajoutés ; décision courte, pas de JSON ni dossier d'architecture obligatoire |
| devops-and-choice | Décrire la livraison depuis les fichiers de cette branche | Identifie CI réelle, mutations et artefacts manquants ; ne migre pas vers GitHub et n'exécute pas `start` |
| postgresql | Ajouter un statut à un CRUD existant | Migration/contrainte et accès ciblés ; pool existant, pas de cache, pgvector ou réplique |
| seaweedfs-s3 | Permettre un petit fichier privé par dossier | Accès lié au propriétaire, taille/contenu bornés ; compare API et transfert direct sans multipart systématique |
| valkey | Le SQL indexé satisfait déjà la latence et la charge | N'ajoute pas de cache ; indique ce qui justifierait de rouvrir la décision |
| casdoor-oidc | Ajouter un droit sur une ressource à une app déjà connectée | Réutilise OIDC/session, applique le droit côté serveur ; pas de nouveau store ou moteur de policy |
| openbao-secrets | L'app utilise seulement PostgreSQL | Lit seulement son secret, sans chemin LLM/OIDC, moteur dynamique ou lecture par requête |
| apisix-llm | Résumer un texte court à la demande | Appel serveur borné avec alias évalué ; pas de RAG, agent, queue ou Temporal par défaut |
| temporal-workflows | Attendre deux jours une décision puis appeler un fournisseur | Workflow/Activity idempotente et budget d'attente ; pas d'outbox sans DB autoritative à synchroniser |
| temporal-operations | Une approbation attend, sans décision et avant échéance | Conclut à l'attente normale, sans reset ni scale-out |
| sdin-umami-instrumentation | Savoir si une nouvelle fonctionnalité est utilisée | Événement de succès minimal ; aucune segmentation/funnel sans question, collecte non bloquante |
| sdin-dozzle-diagnostic | Expliquer une erreur sur une requête connue | Logs bornés en lecture seule, preuve ou observation manquante ; pas de refonte du logger ou redémarrage |
| sdin-registry-delivery | Inspecter l'image et ses artefacts, sans publier | Relie build, handoff, COPY et entrypoint ; ne push ni image ni commit et n'invente pas de digest |

Rejouer aussi le cas opposé quand pertinent : besoin durable réel, latence mesurée
hors budget, charge multi-instance, autorisation révoquée, gros upload ou déploiement
avec contrainte de disponibilité. « Simple » ne doit pas devenir « toujours aucun
service ». L'ajout retenu doit répondre à cette contrainte, avec limite et preuve.

Pour chaque résultat, vérifier : décisions existantes réutilisées, questions vraiment
décisives, service/runtime minimum, paramètres issus du besoin, sécurité conservée,
critère de réévaluation et périmètre d'action respecté. Corriger une contradiction
dans la référence ou l'asset concerné, pas seulement dans le SKILL.md.

## Vérifications locales réutilisables

Les tests d'assets n'appellent pas les services du socle. Avec un Node supportant
le stripping TypeScript (la commande ci-dessous a été utilisée avec Node 22.12) :

```sh
node --experimental-strip-types --test Skills/apisix-llm/assets/llm-client.test.ts Skills/casdoor-oidc/assets/auth-policy.test.ts Skills/openbao-secrets/assets/secret-reader.test.ts
node --test Skills/sdin-umami-instrumentation/assets/track-event.test.mjs
python -B -m unittest discover -s Skills/archi/scripts -p 'test_*.py'
git diff --check
```

Le test Python des liens symboliques requiert que l'OS autorise leur création.
Signaler cette limite si le privilège manque ; ne pas désactiver la protection
du validateur pour obtenir un résultat vert. Le format de chaque SKILL.md et les
liens locaux se vérifient séparément. Les tests Temporal sont décrits dans leur
[référence dédiée](temporal-workflows/references/validation.md).

Ces checks ne prouvent pas les ACL effectives, migrations/contraintes PostgreSQL,
durabilité Valkey, uploads SeaweedFS, login Casdoor live, livraison des événements,
digests publiés ou capacité sous charge. Les vérifier dans l'app et un environnement
autorisé lorsqu'ils conditionnent la livraison ; sinon les marquer non exécutés.
