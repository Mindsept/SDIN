---
name: sdin-umami-instrumentation
description: "Configurer et vérifier une instrumentation Umami légère pour une webapp SDIN dont le service analytics est déjà retenu : navigation, événements, funnels et segmentation adaptée au besoin."
---

# Umami : une collecte proportionnée au parcours

## Résultat attendu

Répondre aux questions produit avec les événements utiles, des données limitées
et une collecte qui ne bloque pas le parcours métier. Le choix d'utiliser Umami
est une entrée du skill ; ne pas ajouter de phase d'arbitrage entre services.

User story : « En tant que responsable produit, je veux comprendre à quelle
étape du panier à la commande les utilisateurs abandonnent, avec un suivi
minimal qui laisse l'application fonctionner si la collecte échoue. »

## Entrées

Recueillir l'app et son domaine, les questions produit, le parcours et ses succès
confirmés, le mode de navigation, le volume attendu, les contraintes de données
et de conservation, et la version Umami réellement utilisée. Rechercher ces
informations dans le brief et l'intégration existante avant de demander un complément.

## Démarche

1. Lire [patterns.md](references/patterns.md) pour choisir les modes d'utilisation
   utiles à la question : navigation, événement de valeur, funnel, segmentation.
   Ne pas appliquer les quatre modes systématiquement.
2. Copier [plan-tracking.yml](assets/plan-tracking.yml) dans l'app et l'adapter.
   Définir le nom, le déclencheur, l'émetteur unique et les propriétés de chaque événement.
3. Pour l'intégration, lire [integration.md](references/integration.md). Réutiliser
   le site et la configuration du socle ; ajouter uniquement l'instrumentation nécessaire.
   L'[adaptateur illustratif](assets/track-event.mjs) convient au funnel donné,
   après adaptation des routes et propriétés à l'app.
4. Exécuter les scénarios pertinents de [validation.md](references/validation.md).
   Mesurer les requêtes émises sur un parcours connu et consigner les résultats réels.
5. Livrer le plan, les changements et les preuves, avec les limites et hypothèses.

## Contraintes essentielles

- Un site distinct par app et un seul chargement du tracker dans la page.
- Émettre un succès après confirmation métier, avec une seule source par événement.
  Ne pas cumuler attribut HTML et appel JavaScript pour la même action.
- Préfixer les événements par `<app>.` ; garder noms et catégories stables.
- Exclure secrets, emails, contenu complet du panier et URLs sensibles. Inspecter
  aussi URL, titre et referrer automatiquement associés par le tracker.
- Ne jamais transmettre le token administratif Umami au navigateur.
- Une erreur de collecte ne doit pas faire échouer la commande, le panier ou la navigation.
  Éviter les reprises non bornées et toute file de collecte ajoutée sans besoin.
- En cas d'interactions fréquentes, suivre validations et résultats utiles plutôt
  que frappes, rendus ou polling. Tout échantillonnage conserve une interprétation
  explicite et cohérente du funnel.
- Définir conservation et fréquence des analyses selon la question et le volume.
  Ne pas annoncer un gain énergétique à partir du seul nombre d'événements.

## Livraison

Fournir le plan de tracking, le site destinataire, les patterns retenus, les points
de déclenchement, les règles de données et les preuves de validation. Signaler les
tests non exécutés. Ne pas démarrer ou purger le socle pour rédiger un plan.
