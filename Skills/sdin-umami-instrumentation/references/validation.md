# Validation Umami

Exécuter sur un site de test identifié et avec des données fictives. Si le socle
est arrêté ou l'app absente, livrer le protocole avec statut « non exécuté ».

| Scénario | Vérification observable |
|---|---|
| Navigation initiale puis transition | Site correct, un tracker, pageviews attendus, chemins normalisés |
| Panier sauvegardé puis commande créée | Noms préfixés, étapes prévues, propriétés autorisées |
| Sauvegarde ou commande refusée | Aucun événement de succès prématuré |
| Double clic / rendu répété / reprise technique | Émetteur unique ; absence de doublon causé par le code de l'app |
| Collecte bloquée ou tracker indisponible | Résultat métier inchangé ; pas de boucle infinie ni erreur non gérée |
| Deux apps sur le même socle | Chaque parcours arrive sur son site et garde son préfixe |
| Route avec identifiant et paramètre sensible fictif | Aucun identifiant ou paramètre sensible dans URL, referrer, titre ou données |

## Preuves

Pour un parcours fixé, relever pages, événements, requêtes analytics et octets
transférés si disponibles. Distinguer un appel d'événement dans le code d'une
requête réseau et d'un événement enregistré par Umami. Expliquer les écarts.
Inspecter les payloads et les résultats du site destinataire, sans publier de
données personnelles dans le rapport.

Une comparaison avant/après utilise le même parcours, les mêmes données et les
mêmes conditions. Elle sert à vérifier la sobriété de collecte ; aucun nombre
universel de requêtes n'est imposé indépendamment du besoin.

## Rapport à fournir

```text
App / version / site / environnement :
Question produit et patterns :
Parcours et répétitions :
Événements attendus / observés :
Requêtes analytics et volume :
Test d'indisponibilité :
Contrôle des données et doublons :
Liens vers les preuves expurgées :
Limites / scénarios non exécutés :
```

Accepter lorsque la question est couverte par les événements prévus, que la
collecte respecte le plan et qu'une panne analytics laisse le parcours fonctionner.
