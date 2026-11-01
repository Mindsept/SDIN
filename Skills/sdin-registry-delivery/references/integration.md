# Intégration Registry au socle SDIN

## Interfaces et limites actuelles

Le [Compose](../../../td/core-platform/podman-compose.yml) fournit Distribution
`registry:2`, le port Linux `5000` et le volume partagé `registry-data`.
Dans l'environnement Mac préparé pour ce TD, le port `15000` est transféré vers
le port `5000` de la VM. Vérifier le contexte et les transferts effectivement actifs.

| Depuis | Adresse habituelle |
|---|---|
| Hôte Linux où tournent Podman et le pipeline | `localhost:5000` |
| Mac avec le transfert configuré | `localhost:15000` |

Le `localhost` d'un conteneur désigne ce conteneur, pas l'hôte. Les références
publiées et déployées doivent être joignables depuis le moteur concerné. Le
registre du TD est local ; ne pas extrapoler une configuration de production.

## Pipeline existant

Le [modèle GitHub Actions](../../../td/core-platform/templates/github-actions.yml) comporte build
explicite, construction/push Podman puis déploiement. Les images sont single-stage.
Le tag issu du commit et les références par tag du
[Compose applicatif](../../../td/core-platform/templates/podman-compose.yml) ne
mettent pas déjà en œuvre une convention de release immuable par digest.

Adapter la CI et les références de l'app lorsque demandé : version de build unique,
enregistrement du digest et déploiement cohérent. Ne pas affirmer qu'il suffit de
copier les templates pour obtenir la preuve « publié = déployé ».

Tracer les vrais artefacts avant l'image : commande productrice, chemin de sortie,
transfert entre jobs, `COPY` et entrypoint. Dans le template, le frontend a un
build Vite ; API/worker utilisent Bun sur les sources TS, sans émission JS établie.
Le job runtime appelle `app-lifecycle.sh` : build, image et publication s'exécutent
sur le même hôte, avec enregistrement des digests. Il ne récupère pas automatiquement
le build du job hosted. Inspecter les artefacts de la bonne exécution sans déduire
leur contenu du modèle. Si l'app sépare producteur et consommateur en plusieurs jobs,
vérifier l'upload/download effectif ; un cache de dépendances n'en est pas la preuve.
Conserver les dépendances natives adaptées à l'OS/architecture de l'image cible.

## Séquence de livraison

1. Relever la provenance, y compris les modifications non commitées. Un commit
   seul ne représente pas un arbre de travail modifié : conserver l'empreinte
   des entrées utilisées et un build_id unique.
2. Préparer les artefacts dans la CI, puis construire les composants nécessaires.
3. Publier dans `<registry>/<app>/<service>:<version>`. Conserver le digest de
   destination annoncé par le push et le confronter au manifeste du registre.
4. Enregistrer ce digest avant déploiement ; préférer une référence `@sha256:…`
   pour le composant concerné si le déploiement le permet.
5. Vérifier depuis le runtime la référence et l'image réellement utilisées,
   puis le démarrage et le parcours. Ne pas comparer directement un image ID
   local à un digest de manifeste : ce sont des objets différents.

Pour une lecture de manifeste, l'API Registry V2 accepte
`HEAD /v2/<app>/<service>/manifests/<version>` avec des types `Accept` appropriés
au manifeste OCI/Docker. Le header `Docker-Content-Digest` correspond à la
représentation obtenue. Utiliser les mêmes types lors des comparaisons.
Pour une image multi-architecture, distinguer digest de l'index et digest du
manifeste choisi ; noter plateforme et preuve correspondante.

Commandes de construction/publication à adapter, uniquement dans une livraison
autorisée et avec les variables définies dans la CI :

```sh
podman build -t "$REGISTRY/$APP/$SERVICE:$TAG" "$SERVICE/"
podman push --digestfile "$DIGEST_FILE" "$REGISTRY/$APP/$SERVICE:$TAG"
```

Vérifier les options de la version Podman installée. `$DIGEST_FILE` est un fichier
de preuve propre au job ; sa valeur vient du pipeline, jamais d'un secret.

## Nettoyage du registre partagé

Inventorier digests et références, protéger déploiements/rollback, puis préparer
les candidats à suppression dans le namespace autorisé. La suppression logique
d'un manifeste et la libération physique de blocs sont deux opérations distinctes.

Distribution peut partager les blocs entre images. Ne jamais supprimer directement
ses fichiers de stockage. Une garbage collection se coordonne au niveau du registre
avec la méthode compatible à la version, une simulation et des écritures suspendues
ou en lecture seule lorsqu'exigé. Une demande de livraison n'autorise pas ce nettoyage.

## Sources

- [API Registry V2](https://distribution.github.io/distribution/spec/api/).
- [Publication Podman 5.7](https://docs.podman.io/en/v5.7.0/markdown/podman-push.1.html).
- [Garbage collection](https://distribution.github.io/distribution/about/garbage-collection/).
- Présentation d'origine : `sdin-skills-services.html`, slide 3 et notes (non incluse dans ce dépôt).
