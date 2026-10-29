---
name: sdin-registry-delivery
description: "Préparer ou vérifier la livraison des images réellement nécessaires dans le Registry SDIN : artefacts de build, digests, réutilisation et rollback. Une inspection n'autorise ni push ni déploiement ; un livrable sans conteneur n'impose pas de registre."
---

# Registry : des artefacts traçables et réutilisables

## Résultat attendu

Construire les composants nécessaires, publier des artefacts traçables et déployer
les mêmes images, avec une rétention qui préserve les versions utiles. Réutiliser
le registre sélectionné et vérifier que la cible consomme des images. Un site statique
livré comme fichiers ne nécessite pas de registre, sauf contrat de déploiement imposant
un conteneur. Aucun SDK registry dans le code métier.

Identifier d'abord l'action autorisée : inspection, build local, publication ou
déploiement. Ne pas passer automatiquement de l'une à la suivante. Commencer par
une image des composants présents et un enregistrement de release ; cache distant,
réutilisation sélective sophistiquée, signatures ou GC automatisée demandent un
besoin de distribution, de fréquence ou une politique applicable. Les digests et
l'absence de secrets restent requis même pour une livraison occasionnelle.

User story : « En tant que développeur, je veux livrer un frontend modifié en
réutilisant l'image API encore valide, puis pouvoir revenir à une version protégée
sans reconstruire une image dont le contenu serait différent. »

## Entrées

Identifier app, composants, contexte d'exécution, registry joignable, sources et
version, entrées de build, déploiement actuel, contraintes de données/migrations
et traitements en cours, versions de rollback et périmètre de publication autorisé.

## Démarche

1. Lire [patterns.md](references/patterns.md) et inventorier les entrées de chaque
   composant avant de conclure à une réutilisation.
2. Pour construire, publier ou vérifier les images, lire
   [integration.md](references/integration.md). Réutiliser le pipeline explicite
   et les images single-stage du TD ; ne pas modifier le socle partagé.
3. Enregistrer provenance, références et digests dans le mécanisme de release existant ;
   utiliser [livraison.json](assets/livraison.json) s'il en manque un.
4. Définir les références protégées dans la politique existante ou [retention.yml](assets/retention.yml).
   Préparer un inventaire de nettoyage ; ne pas déduire une autorisation de
   suppression ou de garbage collection d'une demande de publication.
5. Appliquer [validation.md](references/validation.md) pour identité de l'artefact,
   démarrage/parcours, réutilisation et rollback. Documenter les scénarios non exécutés.

## Contraintes essentielles

- Nom d'image : `<registry>/<app>/<service>:<version>`. Version traçable à un commit
  ou build identifié, y compris pour des modifications locales non commitées.
- Relever l'empreinte de manifeste publiée et vérifier l'artefact effectivement
  déployé. Un identifiant local d'image ne suffit pas à cette preuve.
- Construire une fois et réutiliser ce résultat pour les déploiements concernés.
  Ne pas réécrire un tag déjà déclaré immuable.
- Réutiliser un composant seulement après comparaison de toutes ses entrées :
  sources, dépendances, base, architecture, paramètres, artefacts et fichiers partagés.
- Inclure uniquement code, dépendances runtime et artefacts nécessaires ;
  conserver les fichiers effectivement requis au démarrage et au diagnostic.
- Aucun secret dans les couches ni arguments de build enregistrés dans l'image.
- Vérifier la compatibilité des migrations et traitements en cours avant rollback.
- Protéger versions déployées et rollback. Une purge d'app ne supprime pas
  automatiquement les volumes ni les références d'autres apps dans le registre.
- Coordonner le nettoyage physique du registre partagé selon la procédure du
  mécanisme ; ne pas l'exécuter en parallèle d'écritures incompatibles.
- Mesurer builds, transferts et stockage séparément de la consommation runtime.

## Livraison

Pour une inspection, répondre avec les entrées, références et preuves disponibles.
Pour une livraison autorisée, compléter identité publiée/déployée, réutilisation et
récupération dans le document existant. Créer une politique détaillée de rétention
seulement si elle est en scope. Laisser les digests inconnus non renseignés ; ne pas
inventer une publication ou un rollback réussi.
