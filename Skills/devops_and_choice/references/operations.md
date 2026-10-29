# Operating rules and recovery decisions

Apply these proposed `DVC-*` rules to the selected services only. Keep local workshop configuration distinct from a supported production environment. Use the [runbook template](../assets/operations-runbook.md) to turn each required procedure into an executable, scoped action with an owner and verification.

## 1. Lifecycle, health, and traffic

**DVC-020 — MUST:** validate required configuration at startup, fail with a redacted actionable error, expose `/health` and `/ready` for retained HTTP components, and handle SIGTERM within the platform's ten-second shutdown contract. A static file server can implement simple health endpoints; it does not require a business API. A worker may have a health endpoint without accepting business HTTP requests.

| Condition | Choose | How / why the alternative is wrong |
|---|---|---|
| Process is alive and can execute its event loop | Liveness independent of optional external providers | Do not restart all API replicas because the LLM provider or analytics is unavailable |
| Core requests cannot succeed without PostgreSQL | Bounded dependency/readiness check for the required path | Container creation or open TCP port alone does not establish schema/readiness. Do not check every platform service if the app uses only one |
| Cache is optional and fallback is safe | Keep essential routes ready with bounded fallback, expose degraded status separately | Failing all readiness checks would discard a working authoritative read path; unlimited fallback may overload the DB |
| Only one optional feature is down | Per-feature failure/degradation and telemetry | A whole-app restart hides the actual failed dependency and can amplify it |
| Worker is terminating | Stop taking new jobs, bound current processing, persist/checkpoint or release work according to delivery semantics | Do not acknowledge unfinished work. Define recovery when work cannot finish in ten seconds |
| Long startup/model loading | Explicit startup allowance and resource budget | Do not disable readiness or use liveness restart loops as a loading strategy |

A healthcheck and restart policy are separate settings. Inspect the chosen Podman version and configured behavior; an “unhealthy” status does not universally trigger a restart. Validate readiness and SIGTERM with the actual runtime during integration testing. [Podman health checks](https://docs.podman.io/en/stable/markdown/podman-healthcheck.1.html).

## 2. Capacity, deadlines, retries, and overload

**DVC-021 — MUST:** bound request size, concurrency, connection pools, queue growth, retries and waiting. Derive limits from the accepted workload and the shared host's capacity; do not publish invented universal numeric defaults.

- Compute the maximum DB connections across API replicas, processes, workers, migration jobs and platform services. Choose a smaller measured pool before raising the shared server limit. Add a pooler only for a demonstrated connection-management need and check transaction/session feature compatibility.
- Give each downstream call a deadline within the request's remaining budget; propagate cancellation when supported. Set connect/read/total limits deliberately. Retry transient failures only when the operation is safe or uses an idempotency key; never retry validation, authorization or deterministic schema errors blindly.
- Retry at one deliberate layer with bounded attempts, backoff/jitter and total deadline. Gateway + SDK + app + job retries can multiply external calls and cost. Keep the failed payload/reason for operator diagnosis without exposing secrets.
- Reject or defer excess work with defined semantics (`429`, `503`, or an accepted async job) before exhausting memory. For async acceptance, persist the agreed receipt/state and define queue capacity and overload behavior; do not return success for work that was never durably admitted.
- Set upload size, content/type validation, streaming and temporary-disk bounds. Bound parsing/decompression; a small compressed upload can consume large resources. Choose direct authorized S3 transfer when appropriate; do not buffer large objects into API memory just because the SDK permits it.
- Scale the bottleneck that was measured. More workers can overload PostgreSQL, an LLM quota or S3. Set per-app budgets and leave headroom for shared services, cold starts and deploy overlap.
- Use a cache only with explicit maximum staleness, size/TTL, miss behavior and invalidation. Prefer a constrained fallback or feature degradation when cache outage would otherwise stampede the DB. The shared Valkey instance has no automatically suitable app-specific memory/eviction policy; cache eviction and reliable queue retention may conflict on the same instance.

Record p95/p99 and error rate under a defined workload, resource saturation, and queue oldest age/completion time when relevant. No cache-hit latency, first token, or 202 response substitutes for the promised complete result. See [architecture SLO strategy](../../archi/references/slo-strategy.md).

## 3. Migrations and cross-store consistency

**DVC-022 — MUST:** version every persistent schema change, name the migration owner and serialize its execution. Application replicas must not race destructive migrations during startup. A reviewed explicit migration phase is the default for a shared deployment.

| Requirement | Choose | Procedure and verification |
|---|---|---|
| Local throwaway data, planned downtime allowed | Simple ordered migration | Still test from the previous schema and reject an unexpected database identity; data reset must be explicitly authorized |
| Old/new application versions overlap or quick code rollback is required | Expand → backfill → switch reads/writes → contract later | Add compatible schema first, bound and resume backfill, check counts/invariants, remove old schema only after the compatibility window |
| Large table/index change | Review execution plan, locks and selected server's migration options | Measure on representative data; choose an online operation only when supported and appropriate. Do not assume all DDL is nonblocking or transactional |
| One operation touches PG and S3, or PG and a queue | Durable operation state plus idempotency/reconciliation; transactional outbox when an atomic enqueue intent is required | Commit DB fact and outbox in one DB transaction, publish/retry with stable ID, reconcile duplicates/orphans. Do not pretend a DB transaction includes an S3 upload or Stream append |
| Need undo after a destructive migration | Restore/forward repair plan reviewed before execution | Reverting application code cannot reconstruct dropped business data. A `down` migration is not automatically lossless |

Define transaction boundaries in the application service, not in a controller's incidental call order. Keep network calls outside long DB transactions unless the integrity model specifically requires a bounded coordination mechanism. Apply retention and deletion consistently to source records, S3 objects, vectors, caches and analytics where relevant; include interrupted-delete reconciliation.

## 4. Backups: choose by RPO/RTO, then prove restore

Ask for **RPO** (acceptable lost data/time) and **RTO** (acceptable recovery duration). If undefined, record that recovery guarantees are unknown and propose a reviewable target; do not claim zero-loss recovery from named volumes or AOF alone.

| Selected state | When / how to protect it | Restore verification |
|---|---|---|
| PostgreSQL business records | For modest datasets and acceptable periodic recovery, scheduled logical backups may suffice. For a recovery point between dumps or stricter RPO, assess physical base backups plus continuous WAL archiving and its operational cost | Restore into a separate compatible instance, include required roles/extensions/configuration, validate representative invariants/counts and app queries; measure elapsed recovery and recovered point |
| S3 originals or user files | Separate durable backup/replication/versioning policy only if actually supported/configured for this SeaweedFS deployment; include metadata and credentials/config recovery | Restore a sample of private objects and their ownership metadata; verify contents, authorization and consistency with PostgreSQL |
| Valkey disposable cache | Rebuild from authoritative data; do not spend backup effort preserving invalid cache contents | Clear only the test app's keys in an isolated test, restart, validate safe misses and refill without overload |
| Valkey jobs/session/coordination state | First specify recoverability and allowed loss. Use durable business receipts/outbox/reconciliation where required; inspect AOF policy, volumes and failure scope | Crash/restart recovery, pending entries, duplicate effects and lost-state handling. Persistence on one disk is not protection from that disk's loss |
| Temporal workflow state | Coordinate server persistence backup/recovery with operators; retain compatible worker code and workflow versions | Resume a representative in-flight workflow, verify no repeated non-idempotent external side effect, confirm task queue workers and history compatibility |
| OpenBao secrets | Current dev mode is in memory; restart loses secrets. Treat reseeding/reprovisioning as development recovery, not a durable secrets backup | Verify recovery of required secret identities and update app credentials. For an operated service, separately design persistent storage, key custody, auth/policies, audit and tested recovery |
| Release/configuration | Keep source, reviewed configuration, image digests and compatible prior release artifacts | Recreate runtime and run readiness/smoke against recovered state without introducing production secrets into an insecure test |

**DVC-023 — MUST when durable data matters:** put backups in a separate failure domain with controlled access and retention, record backup age/failure alerts, and perform periodic restores. A backup on the same host does not cover host loss. A raw copy of a running database's volume is not a valid backup unless the database-supported consistency procedure is followed.

PostgreSQL distinguishes logical, filesystem and continuous-archive recovery; dumps cannot be used as the base for WAL replay. Match the actual PostgreSQL 17 deployment rather than assuming a new major version's features. These facts inform the local decision table, not a promise that PITR is configured. [PostgreSQL 17 continuous archiving](https://www.postgresql.org/docs/17/continuous-archiving.html), [backup methods](https://www.postgresql.org/docs/current/backup.html).

## 5. Identity, secrets, networking, and rotation

**DVC-024 — MUST:** distinguish administrator provisioning credentials from application runtime credentials. An app name in a path, key, bucket or namespace is not an access-control mechanism by itself. Describe the actual enforced boundary and any accepted workshop exception.

- Keep secrets on the backend/worker or workload identity boundary. Choose ordinary reviewed configuration for public URLs, feature flags and port numbers. Choose OpenBao for secrets; do not use Valkey or a frontend `.env` as a secret store.
- The repository's OpenBao dev root access and shared service surfaces are local development assumptions. Before claiming independent tenant/workload isolation, configure and test actual policies/authentication. Do not modify the shared server as part of an app plan without the relevant authorization.
- Fetch or inject secrets at controlled startup/refresh points, not on every business request. Set how expiry/revocation triggers refresh, restart or degraded behavior. Verify authentication after rotation; a value changed in OpenBao does not prove every live connection uses it.
- Rotate with overlap when supported: create new scoped credential → deliver it → refresh/restart consumers → verify use → revoke old credential → check failures. For an exposed secret, revoke promptly and investigate use; deleting it from the latest file does not invalidate it.
- Use internal endpoints only for processes on the appropriate network. Browsers use explicitly exposed HTTP routes, never PostgreSQL, Valkey, OpenBao root or raw internal service DNS. Off-host traffic needs the selected target's TLS and authentication model; loopback HTTP in a workshop is not a public ingress configuration.
- Scope user authorization to the requested object/tenant on every relevant access. Casdoor authenticates the user; the API still applies ownership rules. A worker must recheck the current authorization/state when stale queued commands could have become invalid.
- Restrict operator UIs and the Podman socket according to their actual power. Dozzle read-only presentation does not make a mounted management socket a harmless public endpoint. Do not expose consoles through general application routes.

## 6. Observability: choose the signal for the question

| Question | Choose | Do not use as a substitute |
|---|---|---|
| Which route failed and which dependency contributed? | Structured redacted logs with request/trace ID; Dozzle for current container diagnosis | Umami events or unstructured payload dumps |
| Does the SLO hold and are resources near saturation? | Request count/error/latency histogram, workload and pool/queue/resource metrics; a selected metrics collector when continuous operation needs one | Log viewer presence, average latency, successful health check |
| Which distributed step consumed the budget? | Trace spans across relevant boundaries, sampling/redaction appropriate to cost | Tracing every function without an operational question |
| Which feature do users use? | Umami through the documented browser relay where applicable | Durable order/payment state or security audit evidence |
| Who changed a protected business record? | Durable attributable audit event with access/retention and transaction semantics appropriate to the action | Ephemeral stdout, a browser analytics event, or secret-bearing raw request logs |
| Is work stuck? | Queue oldest age, pending/retry/poison counts, workflow task failures and business completion age | Queue length alone: a short queue can contain a permanently stuck item |

**DVC-025 — MUST:** avoid secrets, tokens, unnecessary personal data, raw document prompts and unbounded payloads in logs/analytics. Use bounded low-cardinality metric labels; request IDs, user IDs and arbitrary paths belong in suitable logs/traces, not metric label dimensions. Define retention and access for each signal.

For a workshop demo, scoped structured logs and reproducible measurements may be sufficient. For an operated service with ongoing availability/SLO commitments, select persistent monitoring and alerts with an owner and actionable thresholds. This repository's Dozzle and Umami do not supply a complete metrics, tracing, paging or business-audit system; adding one is an explicit infrastructure decision.

## 7. Stop, purge, deletion, rollback, and incident branches

**DVC-026 — MUST:** inspect and state the scope of an operation before executing it. Reject unexpected environment/app/host identifiers. Never use a global Podman prune, database reset or `FLUSHALL` as a routine app cleanup.

| Intent | Correct branch | Preconditions and completion evidence |
|---|---|---|
| Pause an app/platform temporarily | Corresponding `stop` | State which processes stop and which data remains; verify stopped containers, retained volumes and recovery command |
| Remove app runtime containers/volumes and declared secrets | App `purge` with exact app confirmation | Read actual script: removes app Compose containers/volumes and declared app secret metadata in OpenBao. It retains source/local environment files, shared PG database, S3 bucket and issued identity credentials; deleting stored secret values does not revoke those credentials. List retained resources explicitly |
| Reset the whole platform | Core `purge` with `CONFIRM_PURGE=core` | Destructive shared-volume action affecting all consumers; explicit scope authorization and recoverability required. Never a PR/test default |
| Delete an app's business data | Separate scoped deprovision/retention procedure | Authorized app/tenant/resource inventory, dependency checks, retention decision, explicit delete and verification across selected stores; do not imply app purge does it |
| Bad code release with compatible schema | Redeploy recorded prior digest/config | Verify readiness and representative flow. Template does not provide automatic rollback; implement and test the actual command |
| Bad destructive schema/data change | Halt writes when needed; planned restore or forward repair | Preserve evidence, identify recovery point, validate reconciliation and downstream side effects; code rollback alone is insufficient |
| Cache unavailable | Bounded fallback or degrade optional feature | Avoid DB stampede; verify essential SLO/error behavior; recover scoped keys only |
| Queue/workflow backlog | Reduce producer load, inspect failed/pending work, add workers only within downstream capacity | Reprocess with stable idempotency keys, keep poison items diagnosable; no blind flush/replay |
| Suspected credential leak | Revoke/rotate affected credential and constrain access | Identify impacted processes and data, preserve redacted evidence, verify old credentials fail and new flow succeeds |

Write the runbook from the actual selected deployment, including commands and recovery checkpoints. A proposed plan, a syntax check, a mocked lifecycle test and a real restored deployment are different evidence levels. Official runtime/recovery sources above were consulted on **2026-10-21**.
