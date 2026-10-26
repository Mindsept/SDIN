#!/usr/bin/env bash
# Local and GitHub entry point; keep provisioning in the existing service helpers.
set -euo pipefail
cd "$(dirname "$0")"
ACTION="${1:-start}"
case "$ACTION" in
  check)
    while IFS= read -r -d '' script; do bash -n "$script"; done < <(find . -name '*.sh' -type f -print0)
    exit 0 ;;
  start|stop|purge) ;;
  *) echo 'Usage: lifecycle.sh check|start|stop|purge' >&2; exit 2 ;;
esac
if [[ "$ACTION" == purge && "${CONFIRM_PURGE:-}" != core ]]; then
  echo 'Core purge deletes shared volumes. Set CONFIRM_PURGE=core.' >&2; exit 2
fi
command -v flock >/dev/null || { echo 'Install util-linux (flock).' >&2; exit 1; }
SDI_STATE_DIR="${SDI_STATE_DIR:-$HOME/.local/state/sdi}"
mkdir -p "$SDI_STATE_DIR"
exec 9>"$SDI_STATE_DIR/lifecycle.lock"
flock -w "${SDI_LOCK_TIMEOUT:-300}" 9
trap 'echo "Core lifecycle failed; inspect current state before retrying. No automatic rollback." >&2' ERR

prepare_host() {
  if command -v systemctl >/dev/null && ! systemctl --user start podman.socket; then
    echo 'Podman socket activation failed; check the rootless user session.' >&2
    return 1
  fi
  local config="$HOME/.config/containers/registries.conf"
  mkdir -p "$(dirname "$config")"
  if ! grep -q 'localhost:5000' "$config" 2>/dev/null; then
    printf '\n[[registry]]\nlocation = "localhost:5000"\ninsecure = true\n' >> "$config"
  fi
}

remove_legacy() {
  local container
  for container in redis.internal vault.internal minio; do
    if podman container exists "$container"; then podman rm -f "$container"; fi
  done
}

verify() {
  local attempt code
  for ((attempt=1; attempt<=${SDI_VERIFY_ATTEMPTS:-60}; attempt++)); do
    if curl -fsS --max-time 5 http://localhost:8200/v1/sys/health >/dev/null \
      && curl -fsS --max-time 5 http://localhost:5000/v2/ >/dev/null \
      && curl -fsS --max-time 5 http://localhost:9000/healthz >/dev/null \
      && curl -sS --max-time 5 http://localhost:9080/ -o /dev/null \
      && curl -fsS --max-time 5 http://localhost:9233/ >/dev/null \
      && curl -fsS --max-time 5 http://localhost:9300/ >/dev/null \
      && curl -fsS --max-time 5 http://localhost:9400/api/heartbeat >/dev/null \
      && podman exec valkey.internal valkey-cli ping >/dev/null \
      && podman exec postgres.internal pg_isready -U postgres >/dev/null \
      && podman exec temporal.internal sh -c 'temporal operator cluster health --address $(hostname -i):7233' | grep -q SERVING; then
      code=$(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' \
        -X POST http://localhost:9080/v1/chat/completions \
        -H 'Content-Type: application/json' -d '{"model":"task:cheap","messages":[]}')
      [[ "$code" == 401 ]] || { echo "APISIX key-auth check failed (HTTP $code)." >&2; return 1; }
      echo 'Core readiness and APISIX unauthenticated-access checks passed.'
      return 0
    fi
    sleep "${SDI_VERIFY_INTERVAL:-2}"
  done
  echo 'Core readiness failed after the configured attempts.' >&2
  podman ps --format '{{.Names}} {{.Status}}'
  return 1
}

case "$ACTION" in
  start)
    ./preflight.sh --platform-only
    prepare_host
    if ! podman network exists core-network; then podman network create core-network; fi
    remove_legacy
    [[ -f apisix/apisix.yaml ]] || cp apisix/routes.openai.yaml apisix/apisix.yaml
    podman compose -p core up -d
    # Same dependencies as the old pipeline; serial execution shares one host.
    ./objectstore/seed-admin.sh
    ./temporal/seed-namespaces.sh
    ./idp/seed-and-deploy.sh
    ./apisix/seed-and-deploy.sh
    ./analytics/seed-and-deploy.sh
    verify
    ;;
  stop)
    prepare_host
    podman compose -p core down
    echo 'Core stopped; volumes and network retained.'
    ;;
  purge)
    prepare_host
    podman compose -p core down --volumes
    remove_legacy
    for volume in core_redis-data core_vault-data core_minio-data; do
      if podman volume exists "$volume"; then podman volume rm "$volume"; fi
    done
    if podman network exists core-network; then podman network rm core-network; fi
    echo 'Core runtime and shared volumes removed.'
    ;;
esac
