# Patterns et snippets OpenBao

## Charger seulement les dépendances nécessaires

Copier/adopter `assets/secret-reader.ts` dans le backend. Il lit les chemins KV
v2 explicitement autorisés pour une app, borne sa réponse et refuse redirections
et destinations non approuvées. C'est une protection du client, pas une ACL.

```ts
import { createSecretReader } from "./infrastructure/secret-reader.ts";

const secrets = createSecretReader({
  app: "mon-app",
  address: process.env.VAULT_ADDR ?? "http://openbao.internal:8200",
  token: process.env.VAULT_TOKEN ?? "", // livré au serveur ; aucun fallback root
  allowedSecrets: ["postgres", "llm"],
  allowLocalHttp: process.env.APP_ENV === "development",
});

// Au démarrage : la lecture et la validation précèdent la création du client.
const postgres = await secrets.read("postgres");
const password = postgres.values.password;
if (typeof password !== "string" || password.length === 0) {
  throw new Error("Configuration PostgreSQL absente");
}
// Construire le pool avec les champs validés, puis l'injecter dans les handlers.
// Ne pas console.log(postgres), ne pas retourner cet objet au navigateur.
```

`allowedSecrets`, `app`, `address` et les paramètres d'environnement sont des
configurations serveur. Ils ne viennent pas de query params ni d'un body client.
Un endpoint « lire n'importe quel secret » est exclu même avec ce lecteur.
En production, ajouter le gateway OpenBao HTTPS approuvé via une allowlist
opérateur ; conserver la vérification TLS et ne pas suivre les redirections.

Pour Casdoor, le backend de connexion lit `oidc`. Un worker qui n'effectue pas
de login n'a pas besoin du client OIDC. Pour APISIX, lire `llm` et configurer
l'adaptateur existant : ne pas lire `secret/core/openai` dans l'app.

## Policy runtime minimale

L'asset HCL donne un exemple pour `mon-app` : lecture de `postgres`, `llm` et
`oidc` uniquement. Retirer les chemins inutiles et séparer API/worker si leurs
besoins diffèrent. KV v2 exige le chemin réel `secret/data/...` dans les ACL.

```hcl
path "secret/data/mon-app/llm" {
  capabilities = ["read"]
}
```

Une policy attachée à un token ordinaire limite ses accès. Le token root du TD
ignore cette intention d'isolation ; écrire le fichier HCL ne le remplace pas.
Le provisioning utilise une identité distincte, autorisée seulement à créer ou
mettre à jour les ressources qui lui appartiennent. Ne pas donner `list`,
`delete`, `sudo` ou `secret/*` au runtime sans besoin explicite.

## Création et mise à jour de secrets

Réutiliser `lib/secrets.sh` dans le provisioning autorisé. Ne pas exposer les
valeurs par `set -x`, des arguments de processus ou un fichier versionné.
Le CLI accepte le JSON sur stdin avec `-` et un CAS explicite.
[Commande kv put](https://openbao.org/docs/commands/kv/put/).
Pour créer un secret propre à l'app, cet exemple génère et transmet le JSON
directement sur stdin ; il ne doit être exécuté que pour une création voulue :

```bash
# Depuis td/core-platform/ ; identité de provisioning déjà fournie.
set -euo pipefail
set +x
. ./lib/secrets.sh
python3 - <<'PY' | bao kv put -cas=0 secret/mon-app/session-signing - >/dev/null
import json, secrets
print(json.dumps({"key": secrets.token_hex(32)}))
PY
```

`cas=0` exige une création sans version préexistante ; si elle existe déjà,
ne pas écraser la clé. Ne créer ce secret que si le mécanisme de session choisi
utilise réellement une signature ; une session opaque stockée côté serveur
n'exige pas automatiquement une clé de signature supplémentaire.

Pour une mise à jour concurrente, lire la version, préparer le nouvel état puis
écrire avec le CAS attendu. Un conflit impose une relecture et une nouvelle
fusion, dans une limite de tentatives. Une mutation distante exige d'inspecter
son résultat : un timeout peut laisser l'issue inconnue.
Ne jamais utiliser un fallback `patch || put` pour « réparer » un 403/timeout.
La version KV concerne l'objet entier, pas seulement le champ édité.

## Chargement, refresh et disponibilité

Le runtime conserve en mémoire les seules valeurs nécessaires. Une panne
temporaire d'OpenBao après le chargement n'interdit pas automatiquement toutes
les requêtes avec des credentials encore valides : définir la fraîcheur et le
comportement acceptable selon le secret et le produit. Ne pas cacher une
révocation ni prolonger indéfiniment une identité dont la validité est inconnue.

Un token renouvelable se renouvelle avant son échéance ; une lecture KV statique
ne crée pas de lease à renouveler. Une configuration au démarrage exige un
redémarrage ou refresh explicite pour une rotation. Ne pas étendre ce lecteur
simple en gestionnaire d'AppRole/leases sans besoin et tests correspondants.
[Tokens](https://openbao.org/docs/concepts/tokens/),
[leases](https://openbao.org/docs/concepts/lease/).

## Rotation d'un credential

1. Préparer le nouveau credential dans le service cible et une période de
   coexistence si ce service la permet.
2. Publier la nouvelle version KV, puis recharger les consommateurs concernés.
3. Vérifier leur accès avec le nouveau credential et le comportement de l'app.
4. Révoquer l'ancien dans le service cible, vérifier son refus et terminer la
   fenêtre de coexistence. Traiter l'historique KV selon la politique de rétention.

Si un seul mot de passe peut être actif, coordonner le basculement et sa fenêtre
d'indisponibilité. Un rollback KV vers un ancien mot de passe n'est utile que si
le service cible l'accepte encore. Pour une fuite confirmée, réduire la fenêtre
et révoquer selon le plan d'incident plutôt qu'attendre une rotation ordinaire.

## Tests et preuves

```bash
# Depuis la racine du dépôt, Node avec support TypeScript natif.
node --test skills/openbao-secrets/assets/secret-reader.test.ts
```

Les tests locaux couvrent le lecteur, sans serveur et sans secrets réels.
L'intégration doit en plus prouver, avec une identité runtime limitée : lecture
des chemins nécessaires, refus d'un autre app/core, refus d'écriture, rechargement
après rotation et audit visible. Un succès avec le root de dev ne prouve rien
sur la policy. Ne pas consommer ou révoquer des secrets partagés pour les tests.
