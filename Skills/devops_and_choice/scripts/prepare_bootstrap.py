#!/usr/bin/env python3
"""Prepare an app-owned selective copy; never execute platform operations."""
import argparse
import hashlib
from pathlib import Path
import sys

TEMPLATE_SHA256 = '826b9941e846942fb576f1804e8be6ed332f64f2ef3edb7784c29b7f54a2901f'

PRELUDE = r'''#!/usr/bin/env bash
# App-owned adaptation of SDIN's bootstrap. The platform template is unchanged.
# Review app.env first. No arguments retains the app-lifecycle.sh apply contract.
# --plan validates and prints resource names only; it makes no platform calls.
set -euo pipefail
: "${APP:?APP is required}"
[[ "$APP" =~ ^[a-z][a-z0-9]*(-[a-z0-9]+)*$ && ${#APP} -le 40 ]] || { echo 'Invalid APP name.' >&2; exit 2; }
case "$APP" in
  core|postgres|postgresql|template0|template1|valkey|redis|vault|openbao|s3|casdoor|idp|umami|temporal|temporal-ui|default|registry|dozzle|analytics|platform-admin|platformadmin|anonymous)
    echo 'APP must not be a platform-owned name.' >&2; exit 2 ;;
esac
USE_POSTGRES="${USE_POSTGRES-0}"
USE_OBJECTSTORE="${USE_OBJECTSTORE-0}"
LLM_VKEY="${LLM_VKEY-0}"
TEMPORAL_NS="${TEMPORAL_NS-0}"
ANALYTICS_SITE="${ANALYTICS_SITE-0}"
PUBLIC_BUCKET="${PUBLIC_BUCKET-0}"
for flag in USE_POSTGRES USE_OBJECTSTORE LLM_VKEY TEMPORAL_NS ANALYTICS_SITE PUBLIC_BUCKET; do
  [[ "${!flag}" == 0 || "${!flag}" == 1 ]] || { echo "Invalid boolean flag: $flag" >&2; exit 2; }
done
[[ "$PUBLIC_BUCKET" == 0 || "$USE_OBJECTSTORE" == 1 ]] || { echo 'PUBLIC_BUCKET requires USE_OBJECTSTORE=1.' >&2; exit 2; }
[[ $# -le 1 ]] || { echo 'Usage: bootstrap.sh [--plan|--apply]' >&2; exit 2; }
case "${1:---apply}" in --plan|--apply) ;; *) echo 'Usage: bootstrap.sh [--plan|--apply]' >&2; exit 2 ;; esac
resource_plan() {
  echo "[bootstrap] selected resources for $APP (not runtime verification):"
  [[ "$USE_POSTGRES" != 1 ]] || echo "  postgres: DB/role $APP, secret/$APP/postgres"
  [[ "$USE_OBJECTSTORE" != 1 ]] || echo "  objectstore: bucket/identity $APP, secret/$APP/objectstore, public=$PUBLIC_BUCKET"
  [[ "$LLM_VKEY" != 1 ]] || echo "  llm: secret/core/llm-vkeys[$APP], secret/$APP/llm; gateway activation is separate"
  [[ "$TEMPORAL_NS" != 1 ]] || echo "  temporal: namespace $APP, secret/$APP/temporal"
  [[ "$ANALYTICS_SITE" != 1 ]] || echo "  analytics: site $APP, secret/$APP/analytics"
  if [[ "$USE_POSTGRES$USE_OBJECTSTORE$LLM_VKEY$TEMPORAL_NS$ANALYTICS_SITE" == 00000 ]]; then echo '  none'; fi
  return 0
}
if [[ "${1:-}" == --plan ]]; then resource_plan; exit 0; fi
if [[ "$USE_POSTGRES$USE_OBJECTSTORE$LLM_VKEY$TEMPORAL_NS$ANALYTICS_SITE" == 00000 ]]; then
  resource_plan; echo '[bootstrap] nothing to provision'; exit 0
fi
'''


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('Template structure changed; review the adapter before generating an app copy.')
    return source.replace(old, new, 1)


def adapt(source):
    # Normalise Git checkout line endings; the full reviewed template is pinned.
    source = source.replace('\r\n', '\n')
    if hashlib.sha256(source.encode()).hexdigest() != TEMPLATE_SHA256:
        raise ValueError('Unsupported bootstrap revision. Review the TD diff and adapter tests; do not bypass this guard.')
    body = source.split('set -euo pipefail\n', 1)[1]
    body = replace_once(body, 'for bin in podman openssl; do', '''required_bins=(podman)
if [[ "$USE_POSTGRES$USE_OBJECTSTORE$LLM_VKEY" != 000 ]]; then required_bins+=(openssl); fi
if [[ "$ANALYTICS_SITE" == 1 ]]; then
  required_bins+=(curl python3)
  [[ -x "$CORE_PLATFORM/analytics/site-create.sh" ]] || { echo 'Missing analytics helper: check CORE_PLATFORM.' >&2; exit 1; }
fi
for bin in "${required_bins[@]}"; do''')
    body = replace_once(body, 'echo "[bootstrap] app=$APP — provisioning the core dependencies"',
                        '_bao_resolve\nresource_plan\necho "[bootstrap] applying selected app resources"')
    pg_marker = '# --- 1 + 2. Postgres'
    s3_marker = '# --- 3. The S3 bucket'
    llm_marker = '# --- 7. The LLM virtual key'
    recap_marker = '# --- The recap'
    start, s3, llm, recap = (body.index(marker) for marker in (pg_marker, s3_marker, llm_marker, recap_marker))
    postgres, objectstore = body[start:s3], body[s3:llm]
    # Missing secrets alongside existing resources require reconciliation, not
    # silent password rotation or a new S3 identity that invalidates existing users.
    pg_probe = '''  db_exists="$(psql_root -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$APP'")"
  role_exists="$(psql_root -d postgres -tAc "SELECT 1 FROM pg_user WHERE usename = '$APP'")"
  if [[ -n "$db_exists$role_exists" ]]; then
    echo 'Postgres resources exist without the app secret: restore/reconcile before retrying.' >&2; exit 1
  fi
'''
    postgres = replace_once(postgres, '  pg_password="$(openssl rand', pg_probe + '  pg_password="$(openssl rand')
    objectstore = replace_once(objectstore, 'if s3_shell "s3.bucket.list" | awk',
                              '_sdin_bucket_created=0\n_sdin_bucket_list="$(s3_shell "s3.bucket.list")"\nif printf \'%s\\n\' "$_sdin_bucket_list" | awk')
    objectstore = replace_once(objectstore, '  s3_shell "s3.bucket.create -name=$APP" >/dev/null',
                              '  s3_shell "s3.bucket.create -name=$APP" >/dev/null\n  _sdin_bucket_created=1')
    objectstore = replace_once(objectstore, '  access_key="$(openssl rand', '''  if [[ "$_sdin_bucket_created" != 1 ]]; then
    echo 'S3 bucket exists without the app secret: restore/reconcile before retrying.' >&2; exit 1
  fi
  access_key="$(openssl rand''')
    # Publish anonymous access only after credentials are present/reconciled.
    public_start = objectstore.index('# --- 4. Public read access')
    keys_start = objectstore.index('# --- 5 + 6. The S3 keys')
    public_step = objectstore[public_start:keys_start]
    objectstore = objectstore[:public_start] + objectstore[keys_start:] + public_step
    optional = body[llm:recap]
    # CAS=0 can only create an absent map. A failed PATCH must never replace
    # an existing shared map and erase other applications' virtual keys.
    optional = replace_once(optional, '|| bao kv put secret/core/llm-vkeys',
                            '|| bao kv put -cas=0 secret/core/llm-vkeys')
    return (PRELUDE + body[:start] + 'if [[ "$USE_POSTGRES" == 1 ]]; then\n' + postgres + 'fi\n\n'
            + 'if [[ "$USE_OBJECTSTORE" == 1 ]]; then\n' + objectstore + 'fi\n\n' + optional
            + 'echo "[bootstrap] selected steps completed; verify actual access in the app."\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', type=Path, default=Path(__file__).resolve().parents[3] / 'td/core-platform')
    parser.add_argument('--output', type=Path, required=True, help='New bootstrap.sh in the consuming app; never overwritten')
    args = parser.parse_args()
    try:
        platform = args.platform.resolve()
        output = args.output.resolve()
        repo_td = Path(__file__).resolve().parents[3] / 'td'
        if output.is_relative_to(platform) or output.is_relative_to(repo_td.resolve()):
            raise ValueError('Output must be outside td/ and the platform checkout.')
        result = adapt((platform / 'templates/bootstrap.sh').read_text(encoding='utf-8'))
        with output.open('x', encoding='utf-8') as stream:
            stream.write(result)
        output.chmod(0o755)
    except (OSError, ValueError) as error:
        print(f'prepare-bootstrap: {error}', file=sys.stderr)
        return 1
    print(f'Prepared {output}. Review flags and run --plan; no platform operation was executed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
