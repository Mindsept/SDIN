# Revue des skills — 2 novembre 2026

## Provenance et portée

Base examinée : PR [#4](https://github.com/Mindsept/SDIN/pull/4), commit
`538f5241c7ce236db9ca05b5f4170935516cb562`, puis compléments de validation
sur la même branche. Aucun compte rendu antérieur de challenge n'a été retrouvé
dans les fichiers suivis, l'historique, la description, les commentaires ou les
reviews de la PR. Cela ne prouve pas qu'aucun essai n'a eu lieu ailleurs.
La description de Hugo atteste seulement 45 tests Node locaux et les limites
Windows rencontrées ; ne pas transformer cette déclaration en campagne évaluée.

La passe ci-dessous est une **revue manuelle contextualisée par Codex**, effectuée
en suivant les points d'entrée et références. Les réponses consignées sont les
décisions de cette revue, sans génération d'application ni action sur le socle.
Ce n'est ni un jeu de sorties provenant de modèles indépendants, ni un score de
qualité, ni une validation multi-harness. Les [scénarios](validation.md) restent
le protocole à rejouer pour ces évaluations ultérieures.

## Décisions consignées

Pour chaque ligne, le premier cas reprend le scénario minimal du protocole ;
le contre-cas vérifie que la simplicité ne conduit pas à refuser un besoin réel.
Les renvois identifient les instructions utilisées. Aucun blocage documentaire
n'a été relevé dans ces 26 cas ; les observations nécessitant une app absente
restent expressément à vérifier.

| Entrée lue | Cas minimal : réponse de la revue | Contre-cas : réponse de la revue |
|---|---|---|
| [archi](archi/SKILL.md), [livrables](archi/references/livrables.md) | Page de calcul publique sans persistance : frontend seul et décision courte dans le README ; pas de backend, JSON ou couches vides. | Besoin métier privé avec attente humaine de deux jours : cadrer droits, délai et reprise, puis relayer aux skills concernés ; ne pas déployer les onze services. |
| [devops-and-choice](devops_and_choice/SKILL.md), [livraison](devops_and_choice/references/delivery-github.md) | Décrire cette branche : push/PR isolés, opérations manuelles distinctes ; le runtime reconstruit ses images et ne récupère pas automatiquement le build hosted. Aucun `start`. | Déploiement sur une cible distante : vérifier réseau, registre/TLS, identité de pull et artefacts ; ne pas annoncer que `localhost:5000` y fonctionne. |
| [PostgreSQL](postgresql/SKILL.md) | Ajouter un statut à un CRUD : migration/contrainte et accès ciblés, pool existant ; ni cache ni pgvector. | Invariant soumis à deux écritures concurrentes : contrainte/transaction ou mise à jour conditionnelle, avec test sur PostgreSQL réel ; les mocks ne suffisent pas. |
| [S3](seaweedfs-s3/SKILL.md), [transferts](seaweedfs-s3/references/integration-patterns.md), [R-2-07](CCOE-RULES.md#2-seaweedfs--s3) | Petit fichier privé par dossier : autoriser via le record propriétaire PostgreSQL, flux API borné possible, bucket privé et validation réelle du contenu. | Gros transfert direct : vérifier endpoint navigateur, CORS et limites du stockage ; conserver l'objet en attente/quarantaine et empêcher son remplacement après validation. Pas de garantie inventée à partir d'une URL signée. |
| [Valkey](valkey/SKILL.md), [cache](valkey/references/integration-patterns.md) | SQL indexé déjà dans le budget : aucun cache ; rouvrir le choix si charge/latence le justifient. | Agrégation coûteuse multi-instance avec fraîcheur bornée acceptée : cache partagé candidat, TTL et taille bornés, invalidation et repli limité ; pas de Stream/Worker pour ce seul cache. |
| [Casdoor](casdoor-oidc/SKILL.md) | Ajouter un droit à une app OIDC existante : réutiliser session/client et vérifier l'autorisation objet côté serveur ; pas de nouvel IdP/store. | Révocation rapide entre plusieurs instances : définir invalidation partagée et délai effectif, conserver validation OIDC/CSRF ; un cookie ou rôle envoyé par le navigateur ne constitue pas une preuve. |
| [OpenBao](openbao-secrets/SKILL.md), [patterns](openbao-secrets/references/integration-patterns.md) | App utilisant seulement PostgreSQL : lire uniquement son secret au démarrage avec le loader existant ; aucun chemin LLM/OIDC ou privilège root ajouté. | Credential sous lease/rotation : adopter le renouvellement réellement configuré avec budget borné ; une lease expirée n'est jamais prolongée implicitement. |
| [APISIX](apisix-llm/SKILL.md) | Résumé court : endpoint métier serveur et appel borné via le gateway, alias évalué ; pas de RAG/agent/queue par défaut et aucune clé fournisseur côté navigateur. | Résumé de documents privés : contrôler les droits avant retrieval, borner données/tokens et évaluer le besoin de traitement différé ; une panne ne déclenche aucun secours direct vers un fournisseur. |
| [Temporal workflows](temporal-workflows/SKILL.md), [approbation](temporal-workflows/references/approval-pattern.md) | Attendre deux jours puis appeler un fournisseur : Workflow, Activity idempotente et Worker ; pas de DB/outbox ajoutée uniquement pour l'exemple. | Commit métier autoritatif devant garantir le démarrage : outbox et réconciliation justifiées ; adapter la règle « premier Signal traité » à l'autorité/deadline de la DB. |
| [Temporal operations](temporal-operations/SKILL.md), [diagnostic](temporal-operations/references/diagnostic-matrix.md) | Approbation sans décision avant échéance : attente normale, ni reset ni scale-out. Sans exécution accessible, demander l'observation précise, ne pas inventer son état. | Activity en reprise : vérifier tentative, dernière erreur, timeout et pollers ; ne pas déduire une seule tentative de l'absence d'événements intermédiaires, ni répéter l'effet sans autorisation/idempotence. |
| [Umami](sdin-umami-instrumentation/SKILL.md), [validation](sdin-umami-instrumentation/references/validation.md) | Mesurer l'adoption : un succès métier, noms/propriétés autorisés et collecte non bloquante ; pas de segmentation sans question. | Comprendre l'abandon : quelques étapes de funnel et émetteur unique ; exclure URL/titre/referrer sensibles, vérifier le site destinataire en intégration. Les six tests de double ne prouvent pas la collecte réseau. |
| [Dozzle](sdin-dozzle-diagnostic/SKILL.md) | Erreur connue : consulter des logs bornés par app/période/identifiant et rendre faits/conclusion ; ne pas refondre le logger ou redémarrer. | Corrélation réellement absente : instrumentation ciblée et redaction des secrets, validation sur un parcours fixé ; ni nouveau Worker ni stack de logs par défaut. |
| [Registry](sdin-registry-delivery/SKILL.md), [artefacts](sdin-registry-delivery/references/integration.md) | Inspection d'image : suivre commande → fichiers → handoff → COPY → entrypoint ; relever les inconnues sans push, digest inventé ou déploiement. | Livraison autorisée avec rollback : construire une fois, conserver digest et références protégées, vérifier identité déployée et compatibilité des migrations ; un tag SHA seul n'est pas immuable. |

## Vérifications exécutables

- Documentation : contrôle des liens, métadonnées et routes depuis `AGENTS.md`
  par [le contrôle commun](../ci/check.sh).
- Assets Node : 39 tests APISIX/Casdoor/OpenBao et les 6 tests Umami, désormais
  réunis dans ce même contrôle obligatoire.
- Exemple Temporal : extraction **sans modification** des deux blocs TypeScript
  du guide, compilation stricte contre les packages Temporal `1.25.0`, puis
  [9 tests](../ci/temporal/approval.test.mjs) avec un vrai Worker/Client et des
  Activities doublées sur un serveur jetable. Commande :
  `bash ci/check-temporal.sh` ; installation déterministe via le lock npm.
- Résultat local macOS ARM64 / Node `24.21.0` : 9/9 Temporal réussis, sans exclusion,
  avec CLI `1.9.1` et délais d'entrée courts. La CI Linux utilise le serveur de
  test `1.40.0` avec saut temporel pour exercer l'attente de deux jours.

Les neuf cas couvrent premier Signal valide/conflits précoces, rejet, expiration,
double démarrage actif/clos, entrée invalide, reprise après effet avec même clé,
trois tentatives épuisées, remplacement du Worker pendant l'attente et replay
d'un historique capturé sans exécuter l'Activity.
Les résultats GitHub et leurs journaux sont accessibles depuis la PR ; un succès
local ne remplace pas leur statut obligatoire avant fusion.

## Limites et suite

Aucun service partagé, provisioning, purge ou appel fournisseur n'a été exécuté.
Les tests Temporal prouvent le comportement de cet exemple avec le SDK figé et
un double idempotent, pas l'idempotence d'un fournisseur réel, l'autorisation
métier de l'app, le contenu de son image ni sa capacité sous charge.
La phase de test sur plateforme et l'évaluation comparative entre modèles/harnesses
restent distinctes. Les 26 décisions de revue ci-dessus ne les remplacent pas.
