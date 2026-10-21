# GitHub Actions: choose the execution model and release procedure

The rules marked `DVC-*` are this skill's proposed delivery policy. Repository behavior is identified separately. Inspect the files before acting; a workflow in Git does not prove that a runner, GitHub environment, protection rule, or secret has been configured.

## 1. Actual entry points

| Entry point | Purpose and scope |
|---|---|
| [Repository checks](../../../.github/workflows/checks.yml) | GitHub-hosted checks on pushes and pull requests: shell syntax, architecture validator tests, lifecycle tests using doubles. No shared platform provisioning |
| [Core workflow](../../../.github/workflows/core-platform.yml) | Explicit manual `start`, `stop`, or `purge` on the default branch, using a trusted platform-connected runner and the `sdi-workshop` environment |
| [Core lifecycle](../../../td/core-platform/lifecycle.sh) | Local source of truth for platform lifecycle; start performs provisioning/seeding, stop retains volumes, purge is destructive |
| [Application workflow template](../../../td/core-platform/templates/github-actions.yml) | Copy and adapt as `.github/workflows/app.yml` in the consuming app. Hosted checks and a separate trusted manual lifecycle job |
| [Application lifecycle template](../../../td/core-platform/templates/app-lifecycle.sh) | Copy as `app-lifecycle.sh`; implements `check`, `start`, `stop`, `purge`. Stack-specific example, not a universal application builder |
| [Application settings](../../../td/core-platform/templates/app.env.example) | Copy as `app.env`: reviewed nonsecret settings, selected components, exact tooling version and optional provisioning flags |
| [Requirements](../../../td/core-platform/requirements.md), [app instructions](../../../td/core-platform/templates/README.app.md) | Runner prerequisites, copied auxiliary files and actual command sequence; keep them consistent with the chosen stack |

**DVC-010 — MUST:** decide whether the request is validation, image creation, publication, application deployment, or platform administration. These have different side effects. A PR check must not implicitly bootstrap the shared platform. Running `start` is an operating action, not a syntax check.

## 2. Explicit runner and trigger decisions

| Condition | Choose | Do not choose / why | How and evidence |
|---|---|---|---|
| Lint, unit tests, build checks, dependency checks; code may be untrusted | GitHub-hosted runner with a locked toolchain | Platform-connected self-hosted runner: repository code and dependency install hooks can execute commands | `pull_request`/`push`, read-only token, no platform secrets or shared network. Tests use doubles or disposable test dependencies |
| Integration requires a real database but no shared app state | Disposable isolated PostgreSQL/other selected dependency in the test environment | Existing workshop DB, bucket, or shared Valkey namespace | Create a test database/schema/credentials and deterministic fixtures, apply migrations, clean only that test instance. Match the relevant server/extension version; do not substitute SQLite for PostgreSQL-specific behavior |
| Explicitly operate the developer's existing Podman platform | Trusted self-hosted runner that actually reaches that rootless Podman instance | Hosted runner using `localhost:5000`: that points to itself, not the workshop | Dedicated reviewed execution path, admin-enforced access restrictions, environment configured, preflight and host ownership verified. Current template expects `[self-hosted, linux, sdi-workshop]`; a Mac desktop does not automatically satisfy it |
| Repo accepts code/workflows from untrusted contributors | Keep PR jobs hosted; restrict platform runner access at administration level | Rely only on `if`, labels, branch names, environment secrets, or `clean: false` | Verify allowed repositories and exact trusted workflows/refs where supported. If that boundary cannot be enforced, use a separate trusted operations repo/host and transfer reviewed artifacts. Do not attach the privileged runner to the untrusted repo |
| Delivery to an external managed target is explicitly required | Reachable managed runner or appropriately isolated deployment runner | Assume workshop HTTP registry, private `.internal` DNS, or host socket is reachable remotely | Define registry, TLS/auth, network access, identity and deployment adapter. Add cloud-specific configuration only for that selected target |
| Tests need GPU or unavailable architecture/hardware | Dedicated isolated test runner for that constraint | Reuse a host containing operational credentials just to accelerate tests | Document hardware need, cleanup/isolation and trust boundary. Keep its role distinct from production/workshop administration |

**DVC-011 — MUST:** untrusted content must not execute on a platform-connected runner. This includes checked-out scripts, altered workflow files, package hooks, container builds, artifacts containing executables, and shell-sourced configuration. The app's `app.env` is trusted shell input. Review it as code before runtime use.

The YAML guard protects the supplied job's path; another workflow may attempt to select the same runner. Runner access restrictions are an administrative prerequisite. Check the account/organization's actual available restrictions; labels are routing, not authorization. GitHub documents runner-group controls and the risks of persistent runners. [Runner access](https://docs.github.com/en/enterprise-cloud%40latest/actions/how-tos/manage-runners/self-hosted-runners/manage-access), [secure use](https://docs.github.com/en/actions/reference/security/secure-use).

Use `pull_request` for this harness's ordinary checks. Do not add `pull_request_target` or a privileged `workflow_run` handoff that executes untrusted PR output. If a future metadata-only workflow needs elevated context, separately review its input and execution boundary. [GitHub event guidance](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).

## 3. Local execution and provisioning decisions

The lifecycle scripts are callable locally and by Actions. Copy the complete template set described by `README.app.md`; do not copy only YAML and assume the app has the required scripts, manifests, health endpoints and lockfiles.

- Select the actual `SERVICES` and Compose services together. A static frontend has no implicit API or worker. The supplied bootstrap provisions PostgreSQL and S3 by default; adapt that behavior before executing it for an app that does not use those services. `PROVISION=0` skips provisioning; it does not create missing credentials/resources.
- Choose a distinct lowercase kebab-case app name. The lifecycle rejects platform-owned names such as `postgres`, `casdoor`, `umami`, `temporal`, template databases and shared S3 principals; reusing them can target existing platform credentials/data. Preserve this check when adapting the script and inspect existing resources before onboarding.
- Declare nonsecret defaults in `app.env`; use environment-specific secret delivery for credentials. Never commit `secrets/*.env`, provider keys, or an OpenBao runtime token. A `.gitignore` reduces accidents but does not revoke a previously committed secret.
- Allocate the application's port block and check live conflicts before startup: 8000–8999 in blocks of ten, frontend `+0`, API `+1`, worker health `+8` when present. Exclude 8200–8209 because OpenBao exposes 8200. Different apps must not reuse container names, ports, DBs or buckets.
- Shared seeders and namespace creation belong to a trusted provisioning phase. Normal requests, PR checks and every replica's startup must not recreate identities or mutate shared configuration. Re-seeding may overwrite generated configuration or rotate values: inspect idempotency before claiming rerun safety.
- Keep an operator-owned checkout/location for generated configuration mounted into running containers. The trusted workflow uses `clean: false` to avoid deleting such runtime files; this also preserves stale files. Do not reuse that checkout for untrusted validation. Define reviewed cleanup explicitly, without deleting mounted data.

## 4. Validation gates by component and risk

**DVC-012 — MUST:** write the exact manifest-backed commands, expected inputs, output artifacts and failure behavior for each retained component. “Run tests” is insufficient. The current app template expects TS/Bun-oriented checks; a Python/Java/Go choice requires changing the workflow, lifecycle commands, image recipe and tests together.

| Change / component | Required useful gate | Optional only when justified |
|---|---|---|
| Documentation or skill text | Links, syntax/schema where relevant, one realistic decision exercise for behavioral changes | Do not boot a full platform to validate prose |
| TS/Bun frontend/API/worker | Frozen dependency installation, formatting/lint, type checks, declared unit tests, build for retained components | Browser end-to-end test for important user journeys; no empty worker tests to satisfy a copied template |
| Python backend | Locked dependency install with the selected tool, lint/type checks appropriate to the code, unit tests, package/container build | Full dependency matrix only for supported versions; no Bun command as a substitute |
| JVM/.NET/Go/Rust backend | Project's pinned wrapper/toolchain and real format/static/test/build commands | Cross-architecture testing when deployment architectures differ |
| Authorization, DB or migration change | Real selected database integration tests, unauthorized cross-tenant case, upgrade from previous schema/data, transaction/concurrency case when relevant | Mocks alone cannot validate SQL locks, constraints or migration compatibility |
| Queue/workflow change | Duplicate delivery, retry, worker crash, pending recovery, idempotent effect; replay tests for Temporal changes | A real end-to-end platform run for protocol/config integration, isolated from unrelated apps |
| Caching change | Miss, stale/invalidation, wrong tenant, outage, stampede and bounded fallback; representative latency measurement | Cache-hit benchmark alone is insufficient |
| Release | Secret scan, required app tests/build, image identity, dependency/image findings disposition, health/smoke test and migration status | SBOM/signature/provenance when release policy or distribution needs it; record what is actually generated |
| Performance-sensitive change | Representative workload and data, success/error counts, latency percentile, resource usage, queue completion if relevant | Long benchmark on every tiny edit; repeat only for meaningful risk or a failing gate |

A required test or scanner failure must fail the relevant job. No blanket `continue-on-error`, `|| true`, empty test suite, or ignored migration status to make a release green. Allow a documented, scoped exception with owner/expiry when policy permits it. Do not require a new test solely mirroring a trivial reversible documentation change.

The supplied `p99.ts` reports durations from application logs and the error rate; it is not a traffic generator, a browser journey measurement, or an automatic failure gate solely for exceeding the latency threshold. If the release depends on an SLO, implement an explicit representative measurement and failing acceptance gate. Keep 202 acceptance, workflow completion, and successful full-result latency distinct.

## 5. Secrets, permissions and action supply chain

**DVC-013 — MUST:** start with `contents: read`, disable checkout credential persistence unless a documented action requires it, pin external actions to reviewed full commit SHAs, and pin toolchain versions with lockfiles. Schedule updates through the team's existing dependency process; a pin is not a permanent promise that a version is safe.

Use an environment secret for an authorized deployment credential when a provider has no configured short-lived identity path. Prefer a properly configured short-lived workload identity when the target supports it and its trust policy is established. Request `id-token: write` only for that job. Verify audience and actual subject/repository/ref/environment claims and the target-side permissions. GitHub OIDC does not authenticate user sessions, and the supplied OpenBao dev setup is not automatically configured to trust it. Do not paste an assumed claim format into a trust rule. [GitHub OIDC](https://docs.github.com/en/actions/reference/security/oidc).

Do not expose runtime secrets as browser build variables, cache keys, logs, command tracing, image layers or artifacts. Masking is a fallback, not a storage policy. Bind untrusted expression values through environment variables with validation rather than injecting them into shell source. Treat cache/artifact producers according to their trust level; no privileged execution of a PR-generated script or image.

## 6. Registry, publication, and release identity

| Requirement | Choose | Explicitly reject / integrate |
|---|---|---|
| Local workshop container distribution | Supplied registry, host `localhost:5000`, Podman-network `registry.internal:5000` | No automatic GHCR migration. Local HTTP is a workshop exception, not a remotely exposed default. Verify which hostname the builder and runtime can resolve |
| A remote GitHub-connected deployment must pull images | GHCR is a candidate when that distribution and access model fit; another established registry may be better | Configure package visibility/access, TLS and the runtime's pull identity. Grant `packages: write` only to publishing jobs. Verify the selected target can pull; do not publish as a side effect of a design request |
| Static artifact with no container target | Static build artifact or selected static hosting | Container registry only if the actual runtime consumes an image |
| Repeatable rollback/audit | Build once per release; record source SHA, image digest, migration version and config version | A SHA-shaped tag alone is still mutable. The template's `TAG=github.sha` provides traceability, not enforced immutability. Record the resolved digest and use digest promotion for an operated release |

Dependency caches speed installation and may be discarded. Release artifacts identify what is deployed and need explicit retention/access. Neither is a backup of business data. Set retention for the last known good release and compatibility window; avoid deleting the only rollback image. [GitHub container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## 7. Deployment strategy: explicit branches

- **Recreate on one workshop host:** choose when the product permits a short interruption and the operational model is deliberately simple. Sequence preflight → checks/build → reviewed provisioning/migration → start → readiness/smoke → record release. State the interruption and recovery procedure. The template is a development lifecycle, not a zero-downtime deployment system.
- **Staged/rolling or blue-green deployment:** choose only for an actual availability/rollback requirement and capacity for old/new instances concurrently. Require backward-compatible schema, traffic switching, session/worker coordination and release verification. A second container alone does not implement traffic switching.
- **Kubernetes/Helm:** consider only when an existing target or demonstrated orchestration requirement needs it and someone operates it. Reject for a single workshop host whose needs are met by Podman Compose. Define manifests/probes/resources/secrets and migration ordering if selected; do not claim existing support.
- **Infrastructure as code:** choose when repeatable ownership of multiple real environments/resources justifies it. Begin with existing reviewed scripts for the local lab; do not add Terraform to wrap a single manual command without a resource-state need.
- **Automatic deployment:** add only when explicitly desired and checks, access controls, recovery and target identity are established. The provided workflow is manual. Protect the default branch and sensitive workflow paths through available repository settings and maintainers; YAML cannot assert those settings are enabled.

**DVC-014 — MUST:** serialize mutations of a shared target and never cancel an in-flight migration to make room for another deployment. Current workflow concurrency is repository-scoped. Identical group names in different app repos do **not** serialize a shared Podman host or shared seeders. The supplied core/app scripts also use a shared `flock` at `$SDI_STATE_DIR/lifecycle.lock`, defaulting to `$HOME/.local/state/sdi`; all invocations must use the same rootless user and state directory. Preserve that lock, or use a single controlled operations queue for an alternative target. Define recovery after cancellation; do not delete an unknown lock file to bypass its holder.

Cancel superseded isolated PR checks when useful. Use bounded job and dependency timeouts, but account for what a cancellation leaves behind. Migration locks and idempotent recovery are necessary even with workflow serialization. A failed post-deploy check must report the partial state and safe recovery, not silently claim rollback happened.

## 8. Evidence required for “ready to run”

Record selected workflow/ref, runner owner/OS/reachability, enforced access restrictions, configured environment, secret names (not values), installed tooling, target app/ports, serialized mutation mechanism, selected gates, artifact target, migration command, smoke check and recovery procedure. For workshop-only plans, mark production concerns explicitly out of scope rather than claiming production readiness.

Official GitHub sources above were consulted on **2026-10-21**. The execution decisions and `DVC-*` rules are local harness recommendations, not vendor mandates. Recheck current GitHub features and actual account settings when configuring a new runner or environment.
