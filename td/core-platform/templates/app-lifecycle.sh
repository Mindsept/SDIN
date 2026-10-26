#!/usr/bin/env bash
# Copy to the application root. Local and GitHub runs use the same commands.
set -euo pipefail
cd "$(dirname "$0")"
ACTION="${1:-start}"
case "$ACTION" in check|start|stop|purge) ;; *) echo 'Usage: app-lifecycle.sh check|start|stop|purge' >&2; exit 2 ;; esac
[[ -f app.env ]] || { echo 'Copy app.env.example to app.env and review its settings.' >&2; exit 2; }
set -a
# shellcheck source=/dev/null
source ./app.env
set +a
: "${APP:?APP is required}" "${SERVICES:?SERVICES is required}" "${BUN_VERSION:?BUN_VERSION is required}"
[[ "$APP" =~ ^[a-z][a-z0-9]*(-[a-z0-9]+)*$ && ${#APP} -le 40 ]] || { echo 'Invalid APP name.' >&2; exit 2; }
case "$APP" in
  core|postgres|postgresql|template0|template1|valkey|redis|vault|openbao|s3|casdoor|idp|umami|temporal|temporal-ui|default|registry|dozzle|analytics|platform-admin|platformadmin|anonymous)
    echo 'APP must not be a platform-owned name.' >&2; exit 2 ;;
esac
read -r -a components <<< "$SERVICES"
for component in "${components[@]}"; do
  case "$component" in frontend|api|worker) ;; *) echo "Unsupported component: $component" >&2; exit 2 ;; esac
done
for component in ${INTEGRATION_SERVICES:-}; do
  [[ " $SERVICES " == *" $component "* ]] || { echo 'Integration component is not selected.' >&2; exit 2; }
done
export APP SERVICES
export REGISTRY="${REGISTRY:-localhost:5000}"
[[ "$REGISTRY" =~ ^[a-zA-Z0-9][a-zA-Z0-9.:-]*$ ]] || { echo 'Invalid REGISTRY (host[:port] required).' >&2; exit 2; }
for port in "${FRONTEND_PORT:-8000}" "${API_PORT:-8001}" "${WORKER_HEALTH_PORT:-8008}"; do
  [[ "$port" =~ ^[0-9]{4}$ && "$port" -ge 8000 && "$port" -le 8999 && ( "$port" -lt 8200 || "$port" -gt 8209 ) ]] || {
    echo 'App ports must be in 8000–8999 excluding 8200–8209.' >&2; exit 2;
  }
done
for flag in PROVISION PUBLIC_BUCKET LLM_VKEY TEMPORAL_NS ANALYTICS_SITE; do
  value="${!flag:-0}"
  [[ "$value" == 0 || "$value" == 1 ]] || { echo "Invalid boolean flag: $flag" >&2; exit 2; }
done
for secret in ${APP_SECRETS:-postgres objectstore llm temporal analytics oidc test-users}; do
  [[ "$secret" =~ ^[a-z][a-z0-9-]*$ ]] || { echo 'Invalid app secret name.' >&2; exit 2; }
done
if [[ "$ACTION" == purge && "${CONFIRM_PURGE:-}" != "$APP" ]]; then
  echo 'App purge removes runtime volumes and app secrets. Set CONFIRM_PURGE to APP.' >&2; exit 2
fi

check() {
  [[ "$(bun --version)" == "$BUN_VERSION" ]] || { echo "Expected Bun $BUN_VERSION." >&2; return 1; }
  # Root manifest owns lint tooling; each component declares its actual gates.
  bun install --frozen-lockfile
  bun run lint
  local component scanner
  for component in "${components[@]}"; do
    (
      cd "$component"
      bun install --frozen-lockfile
      bun run typecheck
      bun run test:unit
      bun audit --audit-level=high
      if [[ "$component" == frontend ]]; then bun run build; fi
    )
  done
  scanner=$(./ci/install-gitleaks.sh)
  "$scanner" detect --source . --redact
}

if [[ "$ACTION" == check ]]; then check; exit 0; fi
if [[ "$ACTION" == start ]]; then check; fi
command -v flock >/dev/null || { echo 'Install util-linux (flock).' >&2; exit 1; }
SDI_STATE_DIR="${SDI_STATE_DIR:-$HOME/.local/state/sdi}"
mkdir -p "$SDI_STATE_DIR"
exec 9>"$SDI_STATE_DIR/lifecycle.lock"
flock -w "${SDI_LOCK_TIMEOUT:-300}" 9
trap 'echo "App lifecycle failed; inspect current state before retrying. No automatic rollback." >&2' ERR
podman info --format '{{.Host.Security.Rootless}}' | grep -qi true
podman compose version >/dev/null
# Refuse accidental deployment of components omitted from SERVICES.
actual=$(podman compose -p "$APP" config --services | sort)
expected=$(printf '%s\n' "${components[@]}" | sort)
[[ "$actual" == "$expected" ]] || { echo 'SERVICES and Compose services differ.' >&2; exit 2; }

case "$ACTION" in
  start)
    export TAG="${TAG:-${GITHUB_SHA:-$(git rev-parse HEAD)}}"
    [[ "$TAG" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$ ]] || { echo 'Invalid image TAG.' >&2; exit 2; }
    if [[ "${PROVISION:-1}" == 1 ]]; then ./bootstrap.sh; fi
    if [[ -n "${MIGRATE_SCRIPT:-}" ]]; then bash "$MIGRATE_SCRIPT"; fi
    for component in ${INTEGRATION_SERVICES:-}; do (cd "$component" && bun run test:integration); done
    release="$SDI_STATE_DIR/releases/$APP/$TAG"
    mkdir -p "$release"
    for component in "${components[@]}"; do
      if [[ "$component" == frontend ]]; then
        (cd "$component" && bun install --frozen-lockfile && bun run build)
      else
        (cd "$component" && bun install --production --frozen-lockfile)
      fi
      image="$REGISTRY/$APP/$component:$TAG"
      podman build -t "$image" "$component/"
      podman push --digestfile "$release/$component.digest" "$image"
      grep -Eq '^sha256:[0-9a-f]{64}$' "$release/$component.digest"
      printf '%s\n' "$image" > "$release/$component.image"
    done
    podman compose -p "$APP" up -d --force-recreate
    ready=0
    for ((attempt=1; attempt<=${SDI_VERIFY_ATTEMPTS:-60}; attempt++)); do
      ready=1
      for component in "${components[@]}"; do
        case "$component" in
          frontend) url="http://localhost:${FRONTEND_PORT:-8000}/" ;;
          api) url="http://localhost:${API_PORT:-8001}/ready" ;;
          worker) url="http://localhost:${WORKER_HEALTH_PORT:-8008}/ready" ;;
        esac
        if ! curl -fsS --max-time 5 "$url" >/dev/null; then ready=0; break; fi
      done
      if [[ "$ready" == 1 ]]; then break; fi
      sleep "${SDI_VERIFY_INTERVAL:-1}"
    done
    [[ "$ready" == 1 ]] || { echo 'Application readiness failed.' >&2; exit 1; }
    echo "Application ready; release references recorded in $release."
    ;;
  stop)
    podman compose -p "$APP" down
    echo 'App stopped; secrets, volumes, PostgreSQL and S3 retained.'
    ;;
  purge)
    podman compose -p "$APP" down --volumes
    for secret in ${APP_SECRETS:-postgres objectstore llm temporal analytics oidc test-users}; do
      podman exec -e BAO_ADDR=http://127.0.0.1:8200 \
        -e BAO_TOKEN="${BAO_TOKEN:-root-dev-token}" "${BAO_CONTAINER:-openbao.internal}" \
        bao kv metadata delete "secret/$APP/$secret"
    done
    echo 'App runtime volumes and app secrets removed. PostgreSQL, S3 and issued credentials retained.'
    ;;
esac
