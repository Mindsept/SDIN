# Operations runbook — <application and environment>

Owner/on-call contact: <owner> · Last verified: <date> · Release/config identity: <identity>
Target host/Podman user/network: <exact identity> · Related plan: <link>
Scope: <workshop only / operated environment> · Evidence level: <proposed / tested with doubles / integration-tested / recovery exercised>

Do not execute a placeholder. Replace each command with the actual reviewed application command; omit procedures for unused services. Keep secret values out of this document.

## 1. Before any mutation

1. Verify target host, environment, application name, selected services, ports and current release.
2. Verify the operation is authorized within its exact scope and that shared consumers are accounted for.
3. Acquire the selected deployment/host lock; state how ownership and stale-lock recovery are verified.
4. Inspect current health, migrations and recent failures. Check capacity and required backup/recovery point for a data-changing operation.
5. Identify whether execution is local or via the trusted GitHub workflow. Record the reviewed ref and actual runner access restrictions; labels and environment names alone are insufficient.

## 2. Commands and checkpoints

| Operation | Actual command/workflow, working directory and required nonsecret inputs | Side effects / preserved state | Success check | Failure and recovery checkpoint |
|---|---|---|---|---|
| Isolated checks | <app-lifecycle.sh check or adapted equivalent> | <no shared provisioning> | <gates and artifacts> | <failure blocks which step> |
| Provision selected resources | <reviewed bootstrap/seed subset> | <specific DB/bucket/client/secret resources> | <access test per resource> | <partial provisioning reconciliation> |
| Migrate | <exact migration command> | <schema/data changes; locks> | <migration version and invariants> | <forward repair/restore> |
| Deploy/start app | <app-lifecycle.sh start or selected adapter> | <build/bootstrap/start effects> | <readiness + representative smoke> | <partial state and safe next command> |
| Stop app | <app-lifecycle.sh stop> | <containers stopped; data retained> | <state verification> | <restart path> |
| Purge app runtime, only if requested | <app-lifecycle.sh purge with exact app confirmation> | <inspect script; shared resources retained> | <runtime removed; retained inventory> | <reprovision/redeploy> |
| Core platform lifecycle, if within role | <td/core-platform/lifecycle.sh operation> | <shared platform impact; core purge deletes volumes> | <platform + consumers verification> | <operator recovery procedure> |
| Delete app business data, only if requested | <separate scoped deprovision procedure> | <exact records/objects/identities and retention> | <cross-store deletion verification> | <interrupted deletion reconciliation> |

Environment-specific credentials: <secret names and delivery mechanism, no values>. Required tools/versions: <actual versions>. Runtime configuration location/mounts: <paths and owner>. Clean-up exclusions: <mounted/generated state that must not be deleted by checkout or general cleanup>.

## 3. Health and graceful shutdown

- Liveness: <endpoint, expected result, process-only checks>.
- Readiness: <endpoint, required dependencies, bounded timeout, degraded-feature policy>.
- Startup allowance and failure behavior: <limits>.
- SIGTERM: <stop accepting work, drain/checkpoint, close clients, ten-second contract; tested behavior>.
- Smoke test: <representative authenticated/authorized read/write or static serving path, cleanup scope>.
- Actual restart behavior: <configured policy, healthcheck action and verified runtime version>.

## 4. Capacity and alerting

| Resource/signal | Budget/threshold and why | Owner/action | Evidence |
|---|---|---|---|
| Request latency/errors and workload | | | |
| CPU/RAM/disk/upload/temp-space | | | |
| DB pool/connections/query time | | | |
| Cache hit/miss/staleness/fallback | | | |
| Queue oldest age/pending/retries/completion | | | |
| Provider quota/tokens/cost/deadline | | | |

Log access/redaction/retention: <policy>. Metrics/trace collection: <selected system or workshop measurement procedure>. Product analytics: <Umami only if selected>. Durable business audit: <separate policy if needed>.

## 5. Backup and restore

RPO: <value> · RTO: <value> · Backup failure-domain and access: <location/controls>.

| State | Backup procedure/schedule/retention and owner | Isolated restore command and prerequisites | Integrity/application verification | Last successful exercise and measured recovery |
|---|---|---|---|---|
| <selected durable state> | | | | |

Include PostgreSQL roles/extensions/configuration, S3 objects and owning records, Temporal state/compatible workers and secret recovery where applicable. Record cache rebuild rather than presenting it as business-data recovery. State the development OpenBao restart/reseed limitation. A backup success log alone is not restore evidence.

## 6. Release rollback and data repair

- Known good image digest/config/schema compatibility: <identity>.
- Preconditions for code rollback: <compatible schema and side effects>.
- Exact redeploy/switch command: <command>.
- Post-rollback checks: <readiness, critical flow, errors and data invariants>.
- Irreversible migration or external side effect: <forward repair or restore/reconciliation procedure and authority>.
- Partial deployment/cancel recovery: <which steps may have completed; how to inspect before retry>.

## 7. Incident actions

| Symptom | Diagnose without exposing data | Bounded mitigation | Recovery proof |
|---|---|---|---|
| Database unavailable/saturated | | | |
| Cache unavailable or mass misses | | | |
| Queue/workflow stalled or duplicated effect | | | |
| Object upload orphan/missing content | | | |
| External provider slow/quota exhausted | | | |
| Secret revoked/leaked/rotated | | | |
| Host lost or disk full | | | |

Never substitute a global prune, all-app flush, destructive core purge or blind replay for diagnosis. Escalation owner and condition: <owner and actual trigger>.

## 8. Rotation, retention and retirement

Credential rotation: <create/overlap/distribute/verify/revoke; refresh behavior>.
Data expiry/deletion: <source + objects + vectors + caches + audit constraints>.
Release artifact retention: <preserve compatible rollback versions>.
Retired app inventory: <DB, bucket, keys, secret paths, OIDC client, virtual key, Temporal namespace/task queues, analytics site, images and ports actually allocated>.
Unverified or unknown procedures: <owner and next validation; do not claim guarantees>.
