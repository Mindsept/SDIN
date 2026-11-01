#!/usr/bin/env bash
# Isolated Temporal guide tests: downloads dependencies and a disposable server.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
test_dir="$(mktemp -d "${TMPDIR:-/tmp}/sdin-temporal.XXXXXX")"
trap 'rm -rf "$test_dir"' EXIT
cp "$repo_dir"/ci/temporal/{package.json,package-lock.json,tsconfig.json,extract-example.mjs,approval.test.mjs} "$test_dir/"
cd "$test_dir"
npm ci --ignore-scripts --no-audit --no-fund
node extract-example.mjs "$repo_dir/Skills/temporal-workflows/references/approval-pattern.md"
npm run typecheck
npm run build
npm test
