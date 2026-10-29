# Validation Dozzle et logs applicatifs

Les exemples JSONL sont fictifs, pas des preuves d'exécution de l'application.

| Scénario | Vérification observable |
|---|---|
| Requête REST réussie puis échouée | Résumés avec route, statut, durée et request_id ; cause utile pour l'échec |
| Travail avec reprise autorisée | job_id inchangé, tentative qui évolue, états significatifs retrouvables |
| Incident connu dans deux composants | Parcours retrouvable par les identifiants propagés |
| Donnée sensible fictive dans une entrée ou erreur | Aucune valeur sensible dans les logs, y compris stack traces |
| Boucle / sonde répétée | Pas de trace de succès redondante à chaque itération ; erreurs visibles |
| Debug temporaire | Périmètre respecté et retour constaté au niveau normal |
| Deux apps visibles | Filtre de l'app cible suffisant pour éviter la confusion |

Ne provoquer un échec ou interrompre un travail que dans un scénario de test
autorisé. Un accès en lecture seule permet de valider le diagnostic avec des
traces existantes ; signaler alors les scénarios non provoqués.

## Volume et mesures

Fixer scénario, période et répétitions. Relever lignes et octets émis, producteurs
dominants et doublons éventuels. Comparer une réduction de verbosité sur le même
scénario et confirmer que l'incident reste diagnosticable. Renseigner la politique
de rotation effective, sans la déduire du seul volume visible dans l'interface.

Pour des percentiles, préciser population, unité, nombre d'observations et fenêtre.
Vérifier les données brutes utilisées par la mesure p99. Une sélection de seules
erreurs ou seules requêtes lentes ne représente pas l'ensemble des requêtes.

## Preuves et acceptation

Utiliser [rapport-diagnostic.md](../assets/rapport-diagnostic.md). Inclure un
extrait expurgé, les filtres et le chemin de corrélation ; séparer observation,
hypothèse et cause confirmée. Renseigner « non exécuté » plutôt que simuler une
preuve. Accepter lorsque les scénarios pertinents sont retrouvables, les données
sensibles exclues et la politique de volume compatible avec les mesures requises.
