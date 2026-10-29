# Patterns Umami selon le besoin

Ces modes reprennent navigation, événements, funnels et segmentation classiques.
« Événement de valeur » et « segmentation contrôlée » sont des intitulés
pédagogiques pour ces pratiques, pas de nouveaux standards.

| Besoin | Pattern | Application concrète | Effort évité |
|---|---|---|---|
| Suivre la fréquentation | Suivi de navigation | Un tracker ; routes normalisées ; vérifier les transitions SPA | Doubles pageviews et URLs quasi identiques |
| Mesurer une fonctionnalité | Événement de valeur | `catalogue.cart_saved` après confirmation de sauvegarde | Traces de tous les clics et essais sans résultat |
| Repérer les abandons | Funnel métier | Étapes définies et ordonnées, même périmètre de visiteurs/période | Collecte de détails qui n'expliquent aucune étape |
| Comparer des parcours | Segmentation contrôlée | Catégories telles que `channel=web/mobile_web` | Propriétés libres et cardinalité inutile |

## Adaptations aux contraintes

**Site à navigation classique.** Garder le suivi automatique s'il produit les
URLs attendues. Ne pas ajouter un appel manuel pour les mêmes pageviews.

**SPA ou URLs contenant des identifiants.** Vérifier le suivi des transitions.
Si un mode manuel est nécessaire pour normaliser les chemins, supprimer les
pageviews automatiques correspondants. Remplacer les segments variables par
des routes modèles ; exclure paramètres, fragments et referrers sensibles.

**Parcours transactionnel.** Le clic sur « commander » décrit une intention.
`order_created` décrit une confirmation de création : l'envoyer après la
réponse métier réussie, jamais au seul clic. Une nouvelle tentative technique
de la même action ne doit pas générer une nouvelle émission applicative.
Cela ne garantit pas une livraison exactement une fois par le réseau.

**Interactions nombreuses.** Émettre la sauvegarde validée plutôt que chaque
frappe ou rendu. Pour un autosave, définir ce qui constitue un résultat produit
significatif et éviter d'instrumenter chaque répétition identique.

**Segmentation.** Ajouter une propriété seulement si elle sert une comparaison
nommée. Préférer un petit ensemble stable à une valeur par utilisateur, commande
ou requête. Ne pas identifier une personne pour un simple funnel agrégé.

**Échantillonnage.** Ne pas tirer indépendamment les étapes d'un même parcours :
cela fausserait les taux. Si le besoin l'exige, documenter population, méthode et
biais ; utiliser un mécanisme vérifié sur la version déployée. Le plan exemple
ne comporte aucun échantillonnage.

**Conservation et analyses.** Définir la période utile et le responsable du
nettoyage. Éviter des requêtes répétées sur tout l'historique si une période bornée
répond à la question. Ne pas attribuer au tracker une fonction de rétention qui
n'a pas été vérifiée sur l'installation.

## Exemple de funnel

`catalogue.cart_saved` → `catalogue.checkout_started` → `catalogue.order_created`.
Le premier signifie que le panier a été persisté, le second que le parcours de
commande a commencé, le dernier que l'API a confirmé la création. Vérifier les
parcours qui entrent directement au checkout : un abandon du funnel ne doit pas
être conclu à partir d'une étape qu'ils n'étaient pas censés traverser.

Sources : [événements](https://docs.umami.is/docs/track-events),
[funnels](https://docs.umami.is/docs/funnel).
