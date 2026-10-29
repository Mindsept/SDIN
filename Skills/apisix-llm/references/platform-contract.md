# Contrat APISIX du TD et limites observées

Lecture du dépôt au commit `cde678c`, le 14 octobre 2026. Cette référence décrit
une configuration, pas une certification de son fonctionnement en production.
Relire les sources avant une intégration si elles ont changé.

## Sources de vérité locales

Depuis le dossier `td/` :

| Source | Ce qu'elle définit |
|---|---|
| `core-platform/podman-compose.yml` | Image `apache/apisix:3.17.0-debian`, réseau, port et injection des clés fournisseur |
| `core-platform/apisix/config.yaml` | Mode standalone piloté par fichier, Admin API désactivée, logs d'erreur à `warn` |
| `core-platform/apisix/routes.openai.yaml` | Routes, aliases et plugins de la variante OpenAI |
| `core-platform/apisix/routes.anthropic.yaml` | Variante Anthropic et différences de capacités |
| `core-platform/apisix/seed-and-deploy.sh` | Provider actif, consumers générés, injection des secrets et redéploiement |
| `core-platform/onboard-app.sh` | Clé virtuelle et budget par app, coordonnées runtime, namespace Temporal |
| `core-platform/templates/bootstrap.sh` | Provisioning app, option `LLM_VKEY=1` |
| `core-platform/lib/secrets.sh` | Résolveur CLI OpenBao et accès aux secrets |

La configuration runtime `apisix/apisix.yaml` est générée et gitignorée ; elle
contient des vkeys en clair. Ne pas l'afficher dans un rapport ou la joindre
à une conversation. Une clé virtuelle reste un secret.

## Requête côté application

Dans un conteneur de l'app : `http://llm.internal:9080/v1`.
Depuis l'hôte pour un diagnostic : `http://localhost:9080/v1`.
`localhost` à l'intérieur d'un conteneur désigne ce conteneur, pas APISIX.

Le secret `secret/<app>/llm` contient `base_url` et `virtual_key`.
Envoyer la vkey en `Authorization: Bearer <virtual_key>`.
Les routes convertissent ce header en `apikey` pour `key-auth`.
La clé fournisseur est injectée par la plateforme, pas par l'app.

| Usage | Endpoint POST | Alias | Disponibilité configurée |
|---|---|---|---|
| Texte courant | `/v1/chat/completions` | `task:cheap` | Les deux variantes |
| Texte plus exigeant | `/v1/chat/completions` | `task:quality` | Les deux variantes |
| Analyse d'image | `/v1/chat/completions` | `task:vision` | Les deux variantes ; contrat multimodal à tester |
| Raisonnement complexe | `/v1/chat/completions` | `task:reasoning` | Les deux variantes |
| Vecteurs pour retrieval | `/v1/embeddings` | `task:embed` | Route configurée dans les deux variantes, toujours vers OpenAI ; non validée en réel dans le dépôt |
| Génération d'image | `/v1/images/generations` | `task:image` | Variante OpenAI seulement |

Une route présente ne garantit pas toutes les options du SDK : structured
outputs, outils, streaming et images doivent être validés avec le provider
actif. `/v1/responses`, `/v1/models`, audio et autres API ne sont pas exposés par
ces fichiers. Ne pas les appeler en supposant un proxy universel.
Le client texte fourni avec la skill ne couvre ni vision ni outils ni streaming.

Les noms de modèles concrets restent dans les routes. Ne pas recopier leur liste
dans l'app : le mapping pourra changer et un nom versionné peut être retiré par
le fournisseur. Ne pas présumer des coûts actuels à partir du nom d'un alias.

## Budgets et timeouts

`secret/core/llm-vkeys` est une map app → vkey.
`secret/core/llm-budgets` est une map app → tokens par fenêtre de 60 secondes.
Le seed configure des overrides `ai-rate-limiting` par consumer, avec une valeur
par défaut de 50 000 tokens/60 s. La limite de sortie d'un appel se fixe à part.

Le plugin utilise les tokens remontés après les réponses : une fenêtre n'est
pas une réservation ferme du coût avant l'appel. Des appels en vol peuvent
dépasser le seuil. Les compteurs sont locaux au gateway ; ce n'est ni un plafond
mensuel en euros ni un dispositif distribué persistant. Voir le
[plugin versionné](https://raw.githubusercontent.com/apache/apisix/3.17.0/apisix/plugins/ai-rate-limiting.lua).
Le redéploiement du gateway peut aussi réinitialiser ces compteurs : ne pas
utiliser un re-seed pour contourner un budget épuisé.

Les routes chat fixent notamment une lecture amont à 180 s et le plugin à
180 000 ms. Choisir en plus une deadline totale pour l'opération applicative.
Un timeout socket du gateway ne borne pas à lui seul la durée totale d'un flux.
Les timeouts ne prouvent pas que le fournisseur a cessé de traiter ou de facturer.

## Écarts à ne pas masquer

1. **Egress libre et privilèges de développement.** `core-network` ne fournit
   pas de politique anti-contournement. Le token OpenBao du template est le
   token root de dev, donc le namespace de secrets n'est pas une ACL effective.
   Une isolation de production demande des credentials limités et une politique
   réseau vérifiée, hors de l'intégration app ordinaire.
2. **Aliases ouverts dans les routes.** Le Lua réécrit un alias reconnu, sans
   rejeter systématiquement un nom de modèle brut ou inconnu. La skill impose
   une liste autorisée côté app ; une garantie globale nécessite aussi un rejet
   dans le gateway. Ne pas prétendre qu'il le fait déjà.
3. **Images sans `ai-rate-limiting`.** Cette route utilise `proxy-rewrite` et un
   upstream HTTPS. Les valeurs `n=1`, `quality=low` et `size=1024x1024` ne sont
   que des valeurs par défaut si les champs manquent. Elles ne plafonnent pas
   un client qui fournit autre chose. Prévoir limites serveur et une politique
   image explicite avant d'annoncer un budget image couvert.
4. **Embeddings à valider.** Les routes mentionnent elles-mêmes l'absence de
   validation live. En mode Anthropic, le seed crée un override d'instance
   `anthropic`, mais la route embeddings sélectionne `openai`. Le plugin 3.17
   ignore une instance sans configuration correspondante : le quota embeddings
   doit être corrigé/vérifié avant d'être présenté comme garanti. Ne pas contourner
   le problème en appelant OpenAI directement.
5. **Masquage des credentials à vérifier.** Les routes utilisent `key-auth: {}`.
   `hide_credentials` vaut `false` par défaut ; la route image remplace
   `Authorization` sans retirer explicitement `apikey`. Vérifier ce qui sort
   vers le fournisseur et masquer les credentials d'app dans une évolution de
   plateforme, puis tester la chaîne complète.

Les points 4 et 5 sont des constats de configuration et des risques étayés par
les sources, pas des résultats de tests d'intégration sur une instance active.

## Provisioning et changements

Exécuter depuis `td/core-platform/`, après le démarrage de la plateforme :

```bash
# Chemin recommandé pour une app IA : vkey + budget + secret runtime + re-seed.
./onboard-app.sh mon-app

# À la création seulement : un budget choisi selon le besoin et les mesures.
LLM_BUDGET=12000 ./onboard-app.sh mon-app
```

`onboard-app.sh` conserve une clé et un budget déjà présents : relancer avec
`LLM_BUDGET` ne remplace pas un budget existant. Pour un changement autorisé :

```bash
. ./lib/secrets.sh
bao kv patch secret/core/llm-budgets mon-app=12000
./apisix/seed-and-deploy.sh
```

L'alternative `LLM_VKEY=1` du bootstrap d'app publie la vkey mais ne redéploie
pas APISIX automatiquement ; il faut re-seeder le gateway pour l'activer.
Ne pas remplacer une map globale par `kv put` et perdre les autres apps.

Changer `LLM_PROVIDER` via le seed change le provider de chat pour toutes les
apps. Aucun failover automatique multi-provider n'est configuré ici.
Une rotation/révocation de vkey demande la mise à jour du consumer et du secret
runtime, un re-seed, le rechargement des apps et un test avec l'ancienne clé.
OpenBao est en mémoire : son redémarrage exige un nouveau provisioning même
si PostgreSQL, S3 et les logs d'audit ont persisté.

## Références officielles compatibles avec l'image

- [Mode standalone APISIX 3.17](https://apisix.apache.org/docs/apisix/3.17/deployment-modes/)
- [key-auth 3.17](https://apisix.apache.org/docs/apisix/3.17/plugins/key-auth/)
- [ai-proxy-multi 3.17](https://apisix.apache.org/docs/apisix/3.17/plugins/ai-proxy-multi/)
- [ai-rate-limiting 3.17](https://apisix.apache.org/docs/apisix/3.17/plugins/ai-rate-limiting/)

Les exemples Admin API de ces documentations ne sont pas directement applicables
à la plateforme : elle désactive cette API et utilise ses fichiers et scripts.
