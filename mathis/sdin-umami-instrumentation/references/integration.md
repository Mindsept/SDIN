# Intégration Umami au socle SDIN

## Interfaces à réutiliser

Le [Compose](../../../core-platform/podman-compose.yml) déclare Umami 3.3.1.
Vérifier la version effective avant d'utiliser une option issue de documentation
plus récente. Le [provisionnement existant](../../../core-platform/analytics/site-create.sh)
crée ou réutilise le site nommé exactement comme l'app, puis écrit sa configuration
dans `secret/<app>/analytics`.

| Champ | Usage |
|---|---|
| `website_id` | Identifiant du site, utilisable par le tracker public |
| `event_prefix` | Préfixe `<app>.` des événements |
| `script_url` | `/api/v1/_a/t.js` côté navigateur |
| `collect_url` | `/api/v1/_a/send` côté navigateur |
| `upstream` | `http://analytics.internal:3000` côté serveur |

Le [bootstrap de l'app](../../../core-platform/templates/bootstrap.sh) appelle
ce provisionnement lorsque `ANALYTICS_SITE=1`. Réutiliser cette voie dans une
intégration autorisée ; ne pas créer de nouveau site à chaque démarrage.

## Proxy et tracker

Les chemins sont provisionnés ; cela ne prouve pas que les handlers de l'app
existent. Implémenter ou vérifier leur mapping :

- `GET /api/v1/_a/t.js` → `GET /script.js` sur l'upstream Umami.
- `POST /api/v1/_a/send` → `POST /api/send` sur cet upstream.

Vérifier le navigateur : le tracker ne doit pas déduire un endpoint différent de
`collect_url` depuis le chemin renommé du script. Utiliser une option compatible
avec 3.3.1 ou une adaptation maîtrisée du proxy/tracker, puis constater l'URL
effectivement appelée. Une balise ajoutée seule ne constitue pas une intégration.

Limiter le proxy à ces routes et cet upstream fixe. Conserver l'information de
client utile à l'attribution ; établir les en-têtes de transfert depuis la chaîne
de proxies connue plutôt que faire confiance à un en-tête fourni librement par
le navigateur. Ne pas journaliser le corps de collecte.

Charger le script une fois et sans bloquer le rendu. Publier uniquement la
configuration nécessaire au tracker. Le token administratif reste côté serveur.
Pour le mode manuel de navigation, vérifier `data-auto-pageview="false"` sur
la version utilisée ; ne pas désactiver toute l'initialisation par erreur.

## Événements et exemple fourni

L'[adaptateur](../assets/track-event.mjs) illustre un appel `track(callback)` avec
nom préfixé, route normalisée, données autorisées et erreur absorbée. Il remplace
URL, titre et referrer de cet événement. Il ne configure ni le chargement du
script, ni les pageviews, ni le proxy, ni une déduplication persistante.

L'app l'appelle une fois après le succès confirmé, sans attendre la collecte
pour afficher son résultat. Adapter l'allowlist à la question produit. Le tracker
absent conduit à abandonner l'événement, sans bloquer l'app ; ne pas compenser
par une boucle de réessai non bornée.

## Sources

- [Fonctions du tracker](https://docs.umami.is/docs/tracker-functions).
- [Configuration du tracker](https://docs.umami.is/docs/tracker-configuration).
- [Slides, slide 1 et notes](../../../../presentations/sdin-skills-services.html#slide-1).
