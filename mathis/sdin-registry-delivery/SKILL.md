---
name: sdin-registry-delivery
description: "Préparer et vérifier la livraison d'images dans le Registry SDIN déjà retenu : build explicite, artefacts identifiés par empreinte, réutilisation selon les entrées, rétention et rollback compatibles."
---

# Registry : des artefacts traçables et réutilisables

## Résultat attendu

Construire les composants nécessaires, publier des artefacts traçables et déployer
les mêmes images, avec une rétention qui préserve les versions utiles. Le registre
est déjà retenu ; ne pas ajouter une phase de sélection ou d'arbitrage entre services.

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
3. Adapter [livraison.json](assets/livraison.json) : provenance, références,
   empreintes de manifests et justification des builds ou réutilisations.
4. Définir les références protégées dans [retention.yml](assets/retention.yml).
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

Fournir inventaire des entrées, références et digests observés, décisions de
réutilisation, politique de rétention et preuves de déploiement/rollback. Laisser
les digests inconnus non renseignés ; ne pas inventer une image publiée ou un test réussi.
