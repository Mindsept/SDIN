# Delivery from the actual GitHub/local pipeline

The merged platform uses GitHub Actions and shared local lifecycle scripts.
The `DVC-*` rules remain delivery policy; source files do not prove configured
runners, successful artifact publication or live platform readiness.

## 1. Establish the execution path

| Inspected source | What it establishes |
|---|---|
| [Repository checks](../../../.github/workflows/checks.yml) | Isolated push/PR validation, including skill metadata and documentation navigation |
| [Core workflow](../../../.github/workflows/core-platform.yml) and [lifecycle](../../../td/core-platform/lifecycle.sh) | Manual trusted-host `start/stop/purge`, also callable locally; destructive operations require the exact confirmation |
| [App workflow](../../../td/core-platform/templates/github-actions.yml), [lifecycle](../../../td/core-platform/templates/app-lifecycle.sh) and [settings](../../../td/core-platform/templates/app.env.example) | Isolated hosted checks and a manual runtime job; templates to adapt, not a complete business app |
| [App Compose](../../../td/core-platform/templates/podman-compose.yml) and [bootstrap](../../../td/core-platform/templates/bootstrap.sh) | Proposed components and provisioning defaults, to reduce to selected needs |
| [Requirements](../../../td/core-platform/requirements.md) and [app README](../../../td/core-platform/templates/README.app.md) | Local prerequisites and expected app contracts |

The former GitLab pipeline files have been replaced; see the [migration map](../../../docs/github-migration.md).
A consuming app may still have a different pipeline: inspect its actual files.
Runner registration, environment protections and successful executions require
separate evidence; their presence cannot be inferred from workflow YAML.

**DVC-010 — MUST:** distinguish inspection, isolated validation, local image build,
publication, deployment and platform administration. A request for one does not
authorize all later steps. Do not run the scripts' default `start` to validate a
skill or prose: it provisions and operates shared services. Use isolated checks.

## 2. Choose runners and trust boundaries

Use the existing CI/executor when adequate; a GitHub-hosted repository does not
require GitHub Actions or GHCR. Keep ordinary checks isolated from shared services.
Use disposable databases/test dependencies only for integration behavior needing them.

**DVC-011 — MUST:** do not execute untrusted PR scripts, package hooks, builds or
artifacts on a platform-connected host. Runner labels and job conditions are not
administrative access controls. A hosted runner's `localhost` is itself, not the
developer's registry; private `.internal` names require the actual network.

The provided GitHub path separates hosted checks and a manually dispatched
operating job on `[self-hosted, linux, sdi-workshop]`. Verify runner registration,
administrative access restrictions, target reachability and environment protections.
The YAML declares these requirements; it does not configure them. Local runs use
the same lifecycle scripts.
See [GitHub runner security](https://docs.github.com/en/actions/reference/security/secure-use).

## 3. Trace artifact production and consumption

**DVC-012 — MUST:** map the retained components through:
manifest command → output files → job handoff → image COPY → runtime entrypoint.
Inspect actual run artifacts when available; a YAML declaration is not a produced file.

The app lifecycle runs `bun run build` for the frontend and installs production
dependencies for API/worker (Bun executes TypeScript).
It does not prove emitted `worker.js` or `workflows.js` exists. Read the app's
Dockerfile and build configuration rather than assigning one layout to all stacks.

The runtime job rebuilds and packages on the same host through `app-lifecycle.sh`;
it does not consume the isolated hosted check job's build output. It records
pushed image digests in the release directory. If an app splits producers and
consumers across jobs, it needs an explicit artifact handoff; a shared local
workspace is not evidence that isolated jobs receive the same files.

For an app still using GitLab jobs, declare actual output paths as artifacts and verify the
consumer downloads them through its applicable `needs:artifacts` or
`dependencies` configuration. Do not combine both mechanisms in one job.
For GitHub, use the corresponding explicit upload/download handoff when jobs
are separate. A dependency cache is not proof of a release artifact.
[GitLab artifact behavior](https://docs.gitlab.com/ci/jobs/job_artifacts/),
[dependency configuration](https://docs.gitlab.com/ci/yaml/#needsartifacts).

Keep output paths, relative extraction location, retention and native dependency
OS/architecture aligned with the final image. Missing evidence is a gap to report,
not a reason to fabricate a dist directory or replace the app's CI.

## 4. Gates proportional to the change

| Change | Useful check |
|---|---|
| Skill/documentation | Format/links and representative decision scenarios; no platform boot |
| Pure code or adapter | Real manifest-backed type/lint/unit commands; meaningful failure cases with doubles |
| DB/migration/authorization | Compatible disposable DB and allowed/denied/concurrent paths as applicable |
| Queue/workflow | Retry, duplicate, worker recovery and idempotent effects; replay when relevant |
| Cache | Miss, invalidation, scope, outage and bounded fallback |
| Release | Required app checks, actual image contents/startup, resolved identity and selected smoke/migration checks |
| Performance-sensitive change | Representative measurements of the affected bottleneck, not a benchmark for every prose edit |

Fail the relevant gate on a real required-check failure. Do not invent empty tests,
use blanket `|| true`, or claim mocks prove SQL behavior or provider integration.
Adapt commands to the chosen stack. Paid LLM checks require an authorized budget.

## 5. Credentials and selected CI

**DVC-013 — MUST for GitHub delivery:** begin with minimal token permissions
(`contents: read`), disable unnecessary credential persistence and pin external
actions to reviewed commit SHAs. Preserve the equivalent least-privilege controls
on the existing CI. Pin supported toolchains and dependency versions.

Use the configured secret delivery mechanism, not secrets in build arguments,
bundles, caches or artifacts. Short-lived workload identity is an option only
when its trust relationship is configured; GitHub OIDC does not automatically
authenticate to this OpenBao dev setup. Secret masking does not make disclosure safe.

## 6. Registry and release scope

A static-file target may need no registry. For containers, reuse the selected
registry: the local host endpoint is normally `localhost:5000`; verify the
builder's and puller's network context. Remote distribution may justify a
different registry, TLS and pull identity; do not add it speculatively.

Build once for the release, record source/build provenance and the published
manifest digest, then verify the pulled/deployed identity. A mutable `dev` or
SHA-shaped tag is not enforced immutability. Preserve only the rollback references
and retention required by the app's recovery policy. A local build inspection
does not require a publish, a cleanup system or a full release dossier.
Use [registry delivery](../../sdin-registry-delivery/SKILL.md) for that integration.

## 7. Provisioning, concurrency and recovery

Select only existing app components; the generic bootstrap creates DB/S3 by
default and needs app-scoped adaptation for non-use. The app lifecycle supports
`PROVISION=0` and rejects reserved platform names; skipping provisioning does not
create missing resources. Verify actual settings and exact app/resource identity.

Choose single-host recreate when interruption is acceptable; rolling/blue-green,
Kubernetes or infrastructure-as-code needs an actual operating requirement.
Do not introduce them to deliver one small app.

**DVC-014 — MUST:** serialize mutations of a shared target, and do not cancel a
migration to start another deployment. Core/app scripts use a shared `flock` at
`$SDI_STATE_DIR/lifecycle.lock`; operators must use the same rootless user and state
directory. This complements repository-scoped GitHub concurrency. Verify the lock
is used on the actual host; never delete an unknown lock to bypass its holder.

Inspect stop/purge behavior before use: the core script requires
`CONFIRM_PURGE=core`, and the app script requires its exact app name. These checks
do not authorize deletion; core purge deletes shared volumes. No purge is a test prerequisite. Recovery must distinguish code rollback from
data restore and from irreversible external effects.

## 8. Completion evidence

For the requested scope, report inspected files, executed checks, generated
artifacts and unverified steps. A release additionally needs target/identity,
required gates, migration status, smoke result and recovery reference. Do not
claim a configured runner, uploaded artifact or healthy deployment from source
alone. Preserve workshop-only limitations instead of calling the stack production-ready.
