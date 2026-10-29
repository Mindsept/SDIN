<!-- The canonical app README template — align it with your CCoE rules.
     14 sections, in this order. A section with nothing to report = `None`
     (never deleted). Copy into <app>/README.md and fill it in. -->
# <app-name>

## Overview
<!-- What, for whom, the scope — 3 lines. No marketing pitch. -->

## Getting started
Copy and adapt the complete scaffold from SDIN:

- `templates/github-actions.yml` → `.github/workflows/app.yml`
- `templates/app-lifecycle.sh` → `app-lifecycle.sh`
- `templates/app.env.example` → `app.env` (nonsecret, reviewed shell settings)
- `templates/bootstrap.sh`, `templates/podman-compose.yml` and `templates/gitignore`
- `ci/install-gitleaks.sh` → `ci/install-gitleaks.sh`
- `templates/biome.json` → `biome.json`; selected component sources/Dockerfiles,
  frontend nginx configuration and the appropriate platform libraries/assets.

Use only selected components; align `SERVICES` and Compose. Declare exact Bun
version in app.env. A root package.json with a pinned lint tool and `lint` script,
plus committed lockfiles, is required. Every retained component declares
`typecheck` and `test:unit`; frontend also declares `build`. Selected backends in
`INTEGRATION_SERVICES` declare real `test:integration` against their app-scoped
resources. Add optional migration script via `MIGRATE_SCRIPT`. These files are
scaffolding, not a runnable application with placeholder tests.

```bash
chmod +x app-lifecycle.sh bootstrap.sh ci/install-gitleaks.sh
./app-lifecycle.sh check       # isolated checks, no provisioning
./app-lifecycle.sh start       # checks, provisioning, integration, images, start, readiness
./app-lifecycle.sh stop        # keep data and secrets
CONFIRM_PURGE=<app-name> ./app-lifecycle.sh purge
```

Set `PROVISION=0` only for already provisioned resources. The existing bootstrap
creates PostgreSQL and S3 by default; adapt the copied app bootstrap when those
services are not selected. Set `CORE_PLATFORM` if optional provisioning helpers
need the platform checkout. App environment values are exported for bootstrap
and Compose; never commit credentials in app.env. The runtime runner needs the
exact BUN_VERSION, Podman rootless/Compose, flock and access to the existing core.
GitHub-hosted PR checks do not deploy or access that core. Runtime actions are
manual on the default branch and require configured trusted runner access and
environment protections. Registry defaults to localhost:5000; publication and
Compose share REGISTRY. GitHub uses its commit SHA as TAG; local start uses the
Git commit unless TAG is explicitly supplied. Pushed digests/references are
recorded under `$SDI_STATE_DIR/releases/<app>/<tag>`; tags alone are not immutable.
A release record before failed readiness is not proof of a healthy deployment.

Purge removes app runtime volumes and the listed APP_SECRETS, preserving the
PostgreSQL database, S3 bucket and issued service credentials. It does not revoke
those credentials or delete business data. No automatic rollback is supplied;
record a compatible prior release and its recovery procedure below.

## Design vocabulary
<!-- The core theme (the default) or a justified choice. The
     custom components owned deliberately (outside the daisyUI kit) listed and
     justified here. -->

## Code language
<!-- fr | en — one single choice for the business identifiers. -->

## Tested critical paths
<!-- The journeys covered in integration/e2e, named. They are the ones
     the "no % threshold" doctrine requires covered.
     The test personas (idp/seed-test-users.sh): for each, the username
     <app>-test-<persona>, its scenario, and where the shared password lives
     (secret/<app>/test-users). -->

## Performance
<!-- The 100–350 ms endpoints justified; the endpoints switched to
     202/polling; the p99 measured from the logs. -->

## Personal data register
<!-- The columns, the purpose, the retention, the erasure. None if
     there is no PII. If the app tracks navigation (ANALYTICS_SITE=1), say
     what Umami collects and the value events sent. -->

## External data sources
<!-- One line per third-party source consumed in pull:
     source → the URL of its terms/licence → the attribution required → the
     real publication step → the cache TTL → the fallback (a warm cache /
     fixtures) → the secret path where applicable. None if the app
     consumes no third party. -->

## Exposed interfaces
<!-- REST /api/v1 (the default); WS / gRPC where applicable, with the
     measured criterion. -->

## LLM FinOps
<!-- The vkey, the aliases used, the per-run budget — if it is
     agentic, otherwise None. -->

## Durable workflows
<!-- If the app runs durable workflows, otherwise None:
     the namespace + task queues; the workflow types and, for each, WHAT IT
     WAITS FOR and WHAT IT COMPENSATES; why the engine was needed rather than
     the Stream alone; the VERSIONING POLICY for a deploy with runs
     in flight. Those last two are what a reviewer cannot
     reconstruct from the code. -->

## Libraries outside the recommendations
<!-- lib → what it brings → its cost. None if the stack is 100 %
     recommended. -->

## Structuring decisions
<!-- Lightweight ADRs: 3-5 lines per decision (context → choice →
     consequence). -->

## CCoE waivers
<!-- Granted, justified, dated, with an expiry. None otherwise. -->
