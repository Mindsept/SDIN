# Patterns Dozzle selon le besoin

| Besoin | Pattern classique | Champs / action | Effort évité |
|---|---|---|---|
| Suivre une API REST | Log structuré de requête | Résumé final : request_id, route modèle, statut, durée | Traces répétées à toutes les couches |
| Suivre un worker | Corrélation par tâche | job_id stable, état, tentative, cause des reprises | Une ligne à chaque tour de polling |
| Expliquer un incident | Consultation filtrée | App → composant → période → identifiant | Lecture de tous les logs du socle |
| Investiguer en détail | Debug temporaire | Périmètre ciblé, échéance et rétablissement | Verbosité élevée permanente |

## API REST

Réutiliser le résumé d'accès déjà émis s'il suffit. Associer les événements
pertinents de la requête au même identifiant. Préférer `/orders/:id` à une URL
avec identifiant et paramètres. Un état HTTP ne suffit pas toujours à expliquer
une erreur métier : ajouter un code stable si nécessaire, sans le payload.

INFO pour les faits courants utiles, WARN pour une anomalie ou reprise à surveiller,
ERROR pour l'échec à diagnostiquer, DEBUG pour le détail temporaire. Adapter le
mapping au logger existant ; ne pas doubler une même erreur à chaque couche.

## Worker

Conserver le même job_id entre acceptation, démarrage, reprise et terminaison.
Une tentative supplémentaire est un champ, pas un nouveau job métier. Émettre
les changements d'état ; garder la cause et la tentative d'une reprise utile.
Les noms d'état de l'exemple sont à adapter au traitement réel.

## Contraintes de débit et de mesure

**Faible trafic.** Des résumés complets peuvent être suffisants ; ne pas ajouter
une architecture de collecte ou un échantillonnage par principe.

**Trafic élevé.** Repérer les producteurs les plus bavards et les doublons avant
de réduire. Supprimer les traces sans information nouvelle, normaliser les
champs et définir la rotation. Si un échantillonnage est nécessaire, documenter
population et biais, et préserver les erreurs et les besoins de mesure.

**Sondes et polling fréquents.** Réduire les succès répétitifs sans masquer les
changements d'état ni les échecs. Ne pas demander un p99 global à partir d'un
échantillon limité aux erreurs ou aux requêtes lentes.

**Incident intermittent.** Debug sur composant et périmètre identifiés, avec
durée et personne responsables. Vérifier le retour au niveau normal même si
l'incident disparaît avant son explication.

## Diagnostic

Commencer par un intervalle borné et le composant impliqué. Retrouver la requête
ou le travail, puis suivre son identifiant dans les autres composants. Relever
les faits et les traces absentes. Élargir seulement pour résoudre une question
précise. Conserver un extrait expurgé suffisant à reproduire le raisonnement.

Source : [Dozzle et ses capacités](https://dozzle.dev/guide/what-is-dozzle).
