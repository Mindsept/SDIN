# Exemple à adapter au processus mon-app-api et à attacher à un token non-root.
# Retirer toute dépendance inutilisée ; aucune liste ni écriture au runtime.
path "secret/data/mon-app/postgres" {
  capabilities = ["read"]
}

path "secret/data/mon-app/llm" {
  capabilities = ["read"]
}

path "secret/data/mon-app/oidc" {
  capabilities = ["read"]
}

# Les chemins absents ne sont pas accordés par cette policy.
# D'autres policies attachées au token peuvent accorder davantage de droits.
