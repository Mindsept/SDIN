#!/usr/bin/env bash
# Read-only/offline repository checks: no Podman or external provider required.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -B ci/check_ai_docs.py
python3 -B - <<'PY'
from pathlib import Path
import subprocess
for script in sorted(Path('.').rglob('*.sh')):
    if '.git' not in script.parts:
        subprocess.run(['bash', '-n', str(script)], check=True)
PY
python3 -B Skills/archi/scripts/test_validate_architecture.py
node --test Skills/apisix-llm/assets/llm-client.test.ts \
  Skills/casdoor-oidc/assets/auth-policy.test.ts \
  Skills/openbao-secrets/assets/secret-reader.test.ts
python3 -B -m unittest discover -s ci/tests -p 'test_*.py' -v
