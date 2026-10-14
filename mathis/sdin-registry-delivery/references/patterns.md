# Patterns Registry selon le besoin

| Besoin | Pattern classique | Application concrète | Effort évité |
|---|---|---|---|
| Livrer une version | Build once, deploy many | Publier une image et déployer le même manifeste identifié | Reconstructions entre publication et déploiement |
| Livrer plusieurs composants | Build ciblé | Reconstruire uniquement les composants dont les entrées ont changé | Builds et transferts des composants inchangés |
| Réduire les transferts | Image minimale | Copier les artefacts et dépendances réellement nécessaires | Contextes, couches et fichiers inutiles |
| Maîtriser stockage et rollback | Rétention contrôlée | Protéger versions actives et rollback avant nettoyage | Stockage indéfini et reconstruction d'une version perdue |

## Une seule application ou une livraison occasionnelle

Un inventaire simple et un enregistrement de livraison suffisent. Ne pas ajouter
un système de cache distant ou une automatisation de nettoyage complexe pour
quelques images. La traçabilité reste nécessaire quelle que soit la fréquence.

## Plusieurs composants

Avant de réutiliser l'API lorsque seul le frontend semble modifié, vérifier
lockfile, bibliothèque partagée, définition de build, base et paramètres. Un
fichier partagé peut invalider plusieurs images. Un tag de base inchangé ne
prouve pas que son contenu est inchangé : relever ou épingler son digest.

L'inventaire doit couvrir sources, contexte, définition de build, dépendances,
base, architecture/plateforme, options et artefacts. Si une entrée n'est pas
vérifiable, ne pas annoncer une réutilisation prouvée ; reconstruire le composant
concerné ou recueillir la preuve manquante.

## Livraisons fréquentes

Réutiliser les images valides et protéger les références utiles. Un cache de build
peut aider s'il est déjà disponible et fiable, mais il ne remplace ni l'inventaire
des entrées ni la preuve de l'artefact publié. Mesurer coût de maintien et gain
observé avant d'ajouter une mécanique de cache.

## Taille d'image

Réduire le contexte de build et les fichiers copiés ; exclure sources inutiles,
dépendances de développement, caches et secrets via une liste maîtrisée. Respecter
le single-stage du TD : préparer les artefacts en CI, puis les copier dans l'image.
Tester le démarrage après réduction. Une image plus petite renseigne les transferts
et le stockage ; elle ne démontre pas une baisse de CPU ou mémoire à l'exécution.

## Rétention et rollback

Protéger les digests déployés et les versions nécessaires au rollback, avec les
références de tous les composants concernés. Définir durée ou nombre de versions
selon les livraisons et le besoin de reprise, sans quota arbitraire universel.

Le rollback réutilise une image conservée ; sa compatibilité avec données,
migrations et travaux en cours doit être vérifiée. La conservation de l'image
seule ne suffit pas à garantir un retour fonctionnel.

Sources : [digests](https://docs.docker.com/dhi/explore/security-concepts/digests/),
[garbage collection Distribution](https://distribution.github.io/distribution/about/garbage-collection/).
