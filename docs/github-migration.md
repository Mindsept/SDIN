# GitLab to GitHub: execution and migration map

The former pipelines used GitLab YAML executed locally by `gitlab-ci-local`.
They did not require a GitLab server. Hosting the source on GitHub did not
execute those files. GitHub Actions now calls the same shell lifecycle entry
points used locally. The old pipeline files are replaced, not kept as a second
implementation to maintain.

## What remains the same

- The eleven core services, images, volumes, network and app contracts.
- The existing bootstrap, per-service seeders, helpers and single-stage app images.
- The local Registry at `localhost:5000`; no automatic switch to GHCR or cloud.
- Core `start`, `stop`, `purge`; app provisioning, gates, build, push, deploy,
  readiness, stop and scoped purge.
- Stop retains state. App purge retains the PostgreSQL database and S3 bucket;
  core purge destroys shared volumes. No automatic rollback is added.

## Equivalence of the old stages

| Former GitLab element | GitHub/local equivalent |
|---|---|
| Core `prepare-host` | `lifecycle.sh`: rootless user socket and local HTTP Registry configuration |
| `prepare-network`, `migrate-legacy-services`, `compose-up` | Same named network/container operations, followed by Compose |
| `seed-object-store`, `seed-temporal`, `seed-idp`, `seed-llm-gateway`, `seed-analytics` | The original helper scripts, called in dependency order |
| Core `verify` | Bounded HTTP requests, original service checks, mandatory APISIX 401 check |
| App `variables` | Nonsecret `app.env`, exported by app-lifecycle.sh; TAG from GitHub/local commit |
| App `lint`, `test`, `audit`, `secrets` | `app-lifecycle.sh check`: frozen installs, declared lint/type/unit commands, Bun audit and checksum-verified Gitleaks |
| App `provision`, real integration checks | Manual `start`, after isolated checks; uses the selected app resources |
| App `build-*`, `image-*` | Explicit build and single-stage Podman build/push on the same host; pushed digests recorded |
| App `deploy`, `verify` | Compose recreate followed by readiness for selected components only |
| `ACTION=stop` / `ACTION=purge` | Explicit script argument; purge additionally requires the exact target confirmation |
| GitLab stage barriers and shared filesystem | Ordered steps in one runtime job; no assumption that another hosted job has the same services/artifacts |

The gates are split deliberately: pull-request code must not provision or use
the shared platform. Application manifests must distinguish `test:unit` from
`test:integration`; do not rename live tests to make a PR check appear isolated.
The template targets the existing TS/Bun stack. A justified different language
requires adapting its gates and build exactly as the architecture skill explains.

## Automatic repository CI

[checks.yml](../.github/workflows/checks.yml) runs on pushes and pull requests
on an isolated Ubuntu runner with a read-only repository token. It checks shell
syntax, existing architecture/TypeScript tests, lifecycle behavior with doubles,
and GitHub workflow syntax (including the consuming-app template).

To run its offline checks locally, use `bash ci/check.sh` with Python 3.12 and
Node 24.10.0 (or the supported native TypeScript equivalent). Workflow linting
uses actionlint v1.7.7. These tests do not start Podman, contact a provider, prove
real ACLs, or establish that a workload passes its SLO.

External actions are pinned by commit; toolchain versions and Gitleaks archive
checksums are explicit. Maintain these pins through reviewed updates.

## Manual core operations on the actual workshop host

1. Configure a dedicated Linux runner labelled `self-hosted`, `linux`,
   `sdi-workshop`, owned by the user who runs the rootless Podman platform.
   Check [prerequisites](../td/core-platform/requirements.md); do not use the
   privileged workshop host for untrusted PR execution.
2. At GitHub repository/organization administration level, enforce which trusted
   repositories/workflows/refs may use this runner. Labels and workflow `if`
   conditions alone are not access controls. If the available account controls
   cannot enforce this boundary, use a separate trusted operations repository
   or keep runtime operations local. Do not attach that runner to untrusted code.
3. Configure the `sdi-workshop` environment and appropriate reviewer/branch
   protections. Set optional `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` environment
   secrets only when the selected provider needs them. This workflow does not
   configure GitHub settings, create a runner or grant access on its own.
4. After merging the workflow to the default branch, use Actions → Core platform
   → Run workflow, choose `start`, `stop` or `purge`. Purge requires `core` in
   the confirmation input. It is never a push/PR side effect.
5. The checkout is operator-owned and persistent (`clean: false`): generated
   `apisix/apisix.yaml` is mounted into the running gateway. Do not clean or
   delete that directory while it is in use. It must never be reused for
   untrusted tests; stale files need reviewed, scoped cleanup.

The lifecycle scripts share `$SDI_STATE_DIR/lifecycle.lock`, default
`$HOME/.local/state/sdi/lifecycle.lock`. All app/core operations must use the
same rootless user and directory. This host lock complements repository-scoped
GitHub concurrency; group names alone do not serialize different repositories.
Do not cancel an in-progress mutation to start another one. On timeout/failure,
inspect partial state before retrying; there is no claimed automatic recovery.

## Consuming application migration

Follow the [complete application scaffold instructions](../td/core-platform/templates/README.app.md).
Copy its workflow, lifecycle script, nonsecret settings, bootstrap, Compose and
the [Gitleaks installer](../ci/install-gitleaks.sh). Remove unused components
consistently from `SERVICES`, `INTEGRATION_SERVICES` and Compose. Select actual
manifest-backed test/build commands; the platform does not ship a business app.

Hosted app checks install the exact BUN_VERSION from app.env and never receive
platform secrets. The manual runtime job uses the already installed, same Bun
version on the trusted host and runs everything in one job. It reruns checks
before provisioning, then migrations/integration checks, build, image push,
deployment and readiness. `PROVISION=0` is for existing resources, not a flag
that creates a minimal database-free bootstrap.

Registry and tag are exported to both publication and Compose. The Git commit
tag provides traceability, not enforced immutability. The release directory
records pushed digests/references, including when a later deployment step fails.
Protect compatible prior images and document manual rollback; do not assume a
code/image rollback reverses a database migration or Temporal history change.

Old mentions of GitLab in the course presentation are historical context. The
current scripts, workflow files and this guide describe the executable path.
Runtime integration and platform performance checks remain a separate phase;
a green repository CI establishes only the checks listed above.
