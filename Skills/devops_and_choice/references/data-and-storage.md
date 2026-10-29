# Data and storage: explicit selection rules

Read this reference when choosing persistence, cache, object storage, search, or job state. Apply [scoping](scoping.md) first and record every selected and rejected option in the [service plan](../assets/service-plan.md). `psql` is a PostgreSQL command-line client; PostgreSQL is the database being selected.

Repository baseline: [CCOE-RULES](../../CCOE-RULES.md), especially R-0-01, R-1-01–09, R-2-01–09, R-3-01–09 and R-4-01–04. Those are local rules. The decisions below explain how to apply them; they are not claims that every mechanism is already provisioned. Technical sources and version caveats are in [service-sources](service-sources.md).

## 1. Decide by the meaning of the data

Answer in this order; one application can legitimately select several stores for different data.

1. **Does the application need shared or persistent state?** If no, choose no application database, cache, bucket, or queue. A static site or local calculator does not need PostgreSQL because the platform contains it.
2. **Would losing the data lose an accepted business fact, ownership, a payment status, or an operation to complete?** Choose PostgreSQL for structured authoritative state. A fast store is not a substitute for an integrity contract.
3. **Is the payload a document, image, archive, recording, or generated file?** Choose S3 for the bytes when they must survive container replacement or be shared; keep business ownership, lifecycle, and references in PostgreSQL under the local policy. Public assets bundled in the deployed artifact need no artificial business table or S3 dependency. For public objects served through S3, resolve the policy scope explicitly as described in section 4.
4. **Can the value be recomputed, safely expired, or reconstructed from authoritative data?** Consider Valkey only if a measured performance, coordination, or recoverable job requirement remains after simpler options.
5. **Is there a durable process spanning retries, waits, approvals, or compensations?** Select Temporal using [service-decisions](service-decisions.md), while keeping business records and object bytes in their own stores.
6. **Does the proposal introduce another database, broker, or search engine?** Compare the existing services first. Require a documented unmet requirement, operational owner, migration/reversal plan, and the exception process in the main skill. Novelty or familiarity alone is insufficient.

| Need | Choose | Reject or omit | Reconsider when |
| --- | --- | --- | --- |
| Public static documentation; build-time content | Files in the deployed artifact | Application PostgreSQL, Valkey and S3 if nothing uploads at runtime | Runtime uploads or editorial persistence appears |
| Orders, memberships, ownership, inventories, accepted requests | PostgreSQL with constraints and transactions | Valkey as the only copy; an S3 JSON file as a concurrent relational database | A demonstrated requirement cannot fit the existing database |
| Small single-process transient computation | Request-local or bounded process memory | Shared Valkey without a sharing/performance need | Multiple replicas need common ephemeral state |
| Repeated expensive read; permitted staleness | First optimize PostgreSQL; then bounded cache, optionally Valkey | Caching an unmeasured fast query; stale authorization decisions | Measured miss/hit latency, memory or freshness violates the contract |
| Uploads, reports, source documents | S3 bytes; PostgreSQL metadata for private business objects | Container filesystem as durable storage; Valkey for files | Tiny bounded values need atomic storage with a row, or a missing S3 capability is proven |
| Independent restart-recoverable background jobs | Valkey Streams plus durable operation record/recovery path | Pub/Sub; untracked in-process tasks after an accepted response | Multi-step waits or compensation require Temporal |
| Human approval or durable multi-step process | Temporal | Sleeping HTTP requests; a hand-built orchestration state machine in cache | Process becomes a genuinely independent short job |
| Exact filters, simple lookup, lexical search | PostgreSQL indexes and full-text search when needed | Embeddings for exact IDs; an external search cluster by default | Relevance/features/isolation remain insufficient in representative tests |
| Semantic document retrieval | PostgreSQL + pgvector; S3 originals; APISIX for external embeddings | Valkey documents/chunks/vectors under R-3-09 | Measured filtered recall, latency or scale cannot meet requirements |

## 2. PostgreSQL versus an ORM, SQLite, JSON, or no database

**Choose PostgreSQL** for concurrent mutable records, relational queries, constraints, transactions, durable job status, tenant ownership, or structured data reused by several app components. Use its existing per-app database and role; never store app tables in the Casdoor, Umami, or Temporal databases merely because the same server hosts them.

**Do not choose PostgreSQL** for constants bundled in an artifact, a computation with no persistence, or every large binary payload. A private upload workflow normally needs a metadata record; a public image delivered as a build asset does not.

**Do not replace shared PostgreSQL with SQLite** for a replicated platform backend merely to avoid provisioning. SQLite can fit an offline/local tool or bounded single-process embedded artifact; treat that different deployment model explicitly in [archi](../../archi/SKILL.md). A JSON file fits immutable configuration or an export, not concurrent ownership and transactional updates.

**Choose an ORM** for conventional entity CRUD, relationships and migrations when its integration matches the chosen framework. **Choose a SQL/query builder approach** for a small SQL-focused service, explicit bulk queries, reports, vector operations, or a proven ORM limitation. Both require parameter binding, migrations, transaction boundaries and query evidence. An ORM does not eliminate indexes, N+1 queries, isolation problems or authorization. Use the detailed [ORM rules](../../archi/references/donnees-orm.md) rather than choosing an ORM from the DevOps stack alone.

How to use PostgreSQL:

1. Provision the app database and user; retrieve only `secret/<app>/postgres`. Separate runtime permissions from schema migration permissions where the deployment supports it; do not claim this separation exists until grants are checked.
2. Put ownership/tenant keys, uniqueness, nullability and relationships in the schema. Enforce object authorization on every operation, including list, export and background execution.
3. Define a transaction around one business invariant. Avoid remote calls while holding a database transaction or row lock. Decide how to handle a concurrent update: unique constraint, conditional version update, row lock, or serializable transaction with bounded retry.
4. Apply ordered migrations in delivery, not request handling. Plan expand/backfill/contract when old and new application versions may coexist. Record whether an image rollback remains compatible with the migrated schema.
5. Set pool limits across **all replicas and workers**, connection acquisition deadlines, statement/lock timeouts, pagination and bounded batch sizes. A larger pool can overload the shared database; increasing it is not a universal latency fix.
6. Inspect representative query plans, selected columns, query count, scanned rows and contention before adding a cache. Test realistic tenant distribution and dataset size.
7. Define backup scope, credentials, retention, recovery point objective (RPO: acceptable lost writes) and recovery time objective (RTO: time to restore service). A named Podman volume is not a backup or high availability.

[PostgreSQL constraints](https://www.postgresql.org/docs/17/ddl-constraints.html) provide database-level integrity; [locking](https://www.postgresql.org/docs/17/explicit-locking.html) provides coordination primitives. Their existence does not prove the application uses them correctly.

## 3. Valkey: decide separately for each use case

The current shared service enables AOF and has a volume. Compose does not explicitly set a memory ceiling, eviction policy or per-app ACLs. Inspect actual configuration before promising any loss window, capacity limit or isolation. Key prefix `<app>:` prevents accidental naming collisions; it does not prevent another client from reading a key.

| Use case | Choose Valkey when | Prefer the alternative when | Mandatory design details |
| --- | --- | --- | --- |
| Shared cache | Several replicas reuse costly results and a bounded stale interval is acceptable | Query optimization suffices; one process needs a tiny bounded cache; values must be current | TTL, memory budget, invalidation, tenant-aware key, bounded origin fallback |
| Server session | Several replicas need shared expiring sessions and safe logout on store loss is acceptable | Existing PostgreSQL sessions meet the load and recovery requirement; no login exists | Absolute and idle expiry, cookie policy, rotation, revocation, outage/logout behavior |
| Rate/concurrency counter | Shared short-lived counters protect an app endpoint across replicas | One bounded process limiter is sufficient; the value is a durable entitlement or financial ledger | Atomic update/expiry, actor scope, window, rejection behavior and store-down policy |
| Live presence or transient notifications | Losing an update is acceptable and the client can refresh authoritative state | The event triggers a mandatory action or must replay after disconnection | Expiry, reconnect/resync, no promise of complete delivery |
| Streams job queue | Independent jobs compete among workers, retries are idempotent, and loss/replay has a documented recovery path | Synchronous work fits; a small existing database job table meets the requirement; Temporal process semantics are needed | Durable job ID/status, pending recovery, acknowledgement, retry ceiling, poison handling, retention |
| Duplicate-work suppression | A temporary lease only reduces redundant work and correctness is protected elsewhere | A SQL constraint/conditional write directly enforces the invariant | Unique lease token, expiry, safe release, stale-worker handling |

### Cache choice and freshness

- Start with no cache unless evidence or an explicit forecast establishes the need. Record the baseline, expensive operation and expected reuse; "Valkey is fast" is not evidence that an extra network call helps.
- Specify freshness per value: for example, public catalogue descriptions may tolerate a stated delay; current account permissions or remaining stock must follow the business consistency rule. Never reuse one tenant's cached response for another.
- Prefer cache-aside for reconstructible reads: authorized lookup, bounded cache read, origin load on miss, then bounded write. Invalidate/update after committed changes with a race-aware version or invalidation strategy. TTL alone may not meet immediate consistency.
- Bound entry size, key cardinality, cache penetration and concurrent refresh. Use jitter and coalescing where stampedes are possible. Cache negative results only with a short, explicit lifetime and correct authorization scope.
- On a cache outage, use bounded origin fallback only if the database can tolerate it; otherwise shed load or return a controlled unavailable response. A fallback that opens unlimited database work violates the design.
- Measure cold-cache, warm-cache and recovery bursts. A warm-hit p99 is insufficient evidence for an end-to-end SLO.

### TTL, eviction and durable expectations

- **TTL is an application expiry rule; eviction is a server memory-pressure rule.** Set cache TTLs under R-3-03. For sessions, counters and locks, align expiry to their specific semantics rather than copying a cache TTL.
- Set an explicit total memory plan with the platform owner. Include overhead, persistence buffers and other apps; validate observed usage. Do not change shared `CONFIG` or eviction policy inside app bootstrap.
- An all-keys eviction policy can remove queues, sessions and leases alongside caches. A no-eviction policy can reject writes once its configured limit is reached. A TTL-only policy is not a per-app quota. Do not claim the shared service safely accommodates conflicting requirements without evidence.
- If disposable cache and non-disposable state cannot share one policy, first move the durable state to PostgreSQL/Temporal or redesign recovery. A separately operated Valkey deployment requires an explicit platform decision, ownership and capacity plan.
- AOF settings determine persistence behavior; AOF is neither a separate backup nor a guarantee that every accepted write survives every crash. Record the actual policy and recovery test. If allowed lost work is zero and the deployed queue cannot demonstrate it, durably record accepted operations in PostgreSQL and reconcile them, or change the platform before claiming the requirement is met.

These distinctions follow the vendor's [eviction](https://valkey.io/topics/lru-cache/) and [persistence](https://valkey.io/topics/persistence/) models. The service-selection restrictions are the local harness policy.

### Pub/Sub versus Streams versus a database job table

**Choose Pub/Sub only for disposable notifications.** It has at-most-once delivery; disconnected subscribers miss messages. Send a hint to reload a state, never the only instruction to charge, deliver, or delete. [Valkey Pub/Sub](https://valkey.io/topics/pubsub/)

**Choose Streams under R-3-04 for competing independent idempotent jobs.** Vendor Streams support broader patterns; that does not broaden this harness's default approved pattern. Create an app-prefixed stream and group; workers claim entries, complete durable effects, then acknowledge. Recover abandoned pending work after a defensible idle threshold. Limit attempts and quarantine poison jobs with a durable error/status and an operator procedure. Trim only according to an explicit replay/pending policy, never an arbitrary length that silently removes required work. [Valkey Streams](https://valkey.io/topics/streams-intro/)

**Consider an existing PostgreSQL job table** when enqueue must commit with a business row, job volume is modest, and implementing bounded claiming, recovery, retries and monitoring is simpler than a second store. Document the comparison to the local Stream pattern; this is an application design choice, not an already supplied job-runner implementation. Do not turn the table into an improvised long-lived workflow engine.

**Choose Temporal instead** when progress must survive several dependent stages, durable timers, external signals, human decisions or compensation. A queue and a worker do not alone provide those semantics.

### Idempotency and locks

- Identify an operation with a stable business key and persist its state/result under a unique constraint. Repeating the same key with incompatible input must fail clearly; an idempotency key is not an authorization credential.
- Re-check owner/tenant and current permission before a delayed action. Store small job references in queues; fetch protected data from its authoritative store.
- Prefer PostgreSQL constraints, conditional versions and short transactions for SQL invariants. A distributed lease cannot replace a unique order constraint.
- For a Valkey lease, acquisition expiry plus a unique owner token and compare-before-release prevent deleting another owner's lease. They do not stop an expired holder from later writing to the protected resource.
- If correctness depends on rejecting stale holders, use a monotonically ordered fencing/version token checked atomically by the protected resource, or keep the invariant in a database transaction. Do not advertise a lease library as a correctness proof. The vendor's [distributed-lock page](https://valkey.io/topics/distlock/) is explicitly marked under review; it is not proof of suitability for a critical invariant.

## 4. S3 versus database bytes versus the filesystem

**Choose S3** for uploaded or generated files that need persistence, sharing, controlled download, or independent retention. **Choose bounded PostgreSQL binary storage only by an explicit exception** when small, infrequent bytes need the same atomic transaction as their row and backup/query impact is measured; large business blobs belong in S3 under R-1-02. **Choose the local filesystem** for immutable packaged assets or bounded scratch space whose loss is acceptable. Never promise persistence for a file inside a replaceable API/worker container.

The current SeaweedFS service exposes an S3-compatible API; compatible does not mean every Amazon S3 feature or policy is available in the pinned version. Confirm required operations against the actual image and [SeaweedFS API documentation](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-S3-API).

How to integrate:

1. Use an app bucket and its scoped identity from `secret/<app>/objectstore`. Private is the default. Enable the public-bucket option only for deliberately public assets; never fix a denied private upload by making the bucket public.
2. Use `http://host.containers.internal:9000` from app containers and `http://localhost:9000` from the workshop host. Port 9001 is the filer UI, not the S3 client endpoint. Resolve a separately configured browser-reachable origin before generating browser URLs.
3. Apply R-2-07: authorize each upload/download/overwrite/delete against the owning PostgreSQL record before issuing access or a signed URL. Random or app-prefixed keys are not authorization. Store opaque/generated keys, owner, content type, size, checksum where required, state and retention metadata. The rule is written for every object operation, while R-2-03 permits an explicitly public bucket. Do not silently narrow R-2-07 to private objects: for public S3 assets, record the apparent scope conflict and obtain the actual policy owner's interpretation or exception if required. Bundling public build assets in the deployment avoids this S3 policy question entirely.
4. For small bounded uploads, API proxying can simplify authorization and validation. For larger files, a short-lived scoped presigned operation can remove API bandwidth pressure **only after** browser reachability, CORS, supported signing semantics, upload limits and completion validation are tested. Never hand browser clients bucket access keys.
5. Enforce byte/count limits before unbounded buffering; validate actual type and untrusted filenames. If scanning/quarantine is required, do not expose the object until that step succeeds. Treat presigned URLs as bearer capabilities and keep them out of logs.
6. Define multipart abort/expiry, orphan cleanup, replacement/version policy and authorized deletion. Do not assume bucket versioning, lifecycle policies, encryption configuration or replication are already enabled.
7. Track temporary disk quotas and cleanup if transformations need scratch files. Pass object references to workers instead of file bytes in job payloads or workflow history.
8. Back up both object data and the metadata needed to locate and authorize it; verify a restore can re-establish the relationship. A bucket's existence or a successful PUT does not demonstrate recoverability.

## 5. Consistency across PostgreSQL, S3 and a queue

There is no shared atomic transaction across these services (R-4-01). Choose and document a sequence that can be retried and reconciled.

| Scenario | Required sequence | Failure/retry rule |
| --- | --- | --- |
| Accept a job coupled to a row update | Commit business state plus operation/outbox record together; dispatch after commit | Retry dispatcher using stable IDs; consumers deduplicate; reconcile undispatched/stalled records |
| Accept an upload | Create authorized pending metadata; upload bytes; verify completion; mark available | Pending state is not a successful document; expire orphan objects/rows after a stated interval |
| Generate a report | Record operation; write result to deterministic/versioned object key; commit available metadata | A retry must not create multiple visible reports or expose half-finished results |
| Delete a private document | Revoke visibility/access first; mark deletion pending; delete object and derived copies; finalize | Repeated delete is safe; reconcile storage failures; preserve minimal required deletion evidence |
| Update a cached record | Commit authoritative row; invalidate/version cache according to freshness requirement | Recover a missed invalidation; do not publish uncommitted values |

Use an outbox when a durable database commit must imply eventual dispatch. A single `UPDATE` followed by a queue write has a crash gap; reversing the order has a different gap. An outbox reduces that gap but does not make the consumer effect exactly once. Apply idempotency at the actual effect, including external APIs when supported.

## 6. Search: none, SQL, full-text, pgvector, or a separate engine

| Query requirement | Default choice | Explicit reason to reject another choice |
| --- | --- | --- |
| Exact identifier, date range, owner, status or category | SQL with suitable indexes | Embeddings add cost and approximate answers to an exact question |
| Small bounded prefix/substring use case | Measure an appropriate PostgreSQL query/index first | Do not create a search cluster before the existing query fails its requirement |
| Language-aware lexical document search and ranking | PostgreSQL full-text search with the intended text configuration and index | Plain equality does not provide lexical search; semantic embeddings are not necessary for every keyword search |
| Similar meaning, retrieval-assisted answers, semantic recommendations | pgvector with recorded model, dimension, distance and evaluation dataset | Lexical-only search may miss paraphrases; vector-only retrieval may miss exact codes or names |
| Both exact/lexical and semantic relevance | Evaluate hybrid retrieval and authorization-aware merging in PostgreSQL | More retrieval stages require measured quality/latency benefit |
| Specialized relevance, search isolation or scale beyond tested PostgreSQL capabilities | Propose a separate engine as an exception with synchronization and rebuild ownership | Product popularity and an arbitrary row-count threshold are not sufficient evidence |

PostgreSQL [full-text search](https://www.postgresql.org/docs/17/textsearch.html) and [pgvector](https://github.com/pgvector/pgvector) cover different query semantics. For vectors, start with the simplest adequate search; add approximate indexes only after measuring latency and recall, including tenant filters. Index choice does not remove permission filtering or guarantee acceptable filtered recall.

For RAG under R-3-09: originals belong in S3; document metadata, chunks and embeddings belong in PostgreSQL/pgvector; Valkey holds small recoverable job references or permitted ephemeral coordination, **not documents, chunks or vectors**. Record source revision and embedding model/version. A model/dimension change needs an explicit reindex/backfill and cutover plan. Deleting/revoking a source must remove or suppress its chunks, vectors, cached outputs and downloads. Evaluate retrieval with realistic unauthorized documents present, not only a single-user corpus.

## 7. Let latency, availability and recovery change the choice

Use [archi's SLO strategy](../../archi/references/slo-strategy.md) for the language/framework/architecture decision. Here, explicitly ask for endpoint latency percentile and threshold, measurement boundary, traffic/concurrency, acceptable staleness, error rate, RPO/RTO, and background completion time. Unknown targets remain assumptions to validate.

- If a SQL route meets its target under representative load, omit Valkey. If it misses because of scans/N+1/locks, fix that cause first. If repeated expensive reads still miss and stale results are allowed, evaluate cache. If freshness must be immediate, choose a consistency-preserving query/model change before caching.
- If object transfer dominates response time, distinguish metadata acknowledgement from full upload completion. A direct upload may remove API work; it does not make the user's transfer instantaneous.
- If work cannot reliably complete inside the request deadline, accept it durably and return a job reference only when the product permits asynchronous completion. Define both acceptance and completion SLOs, status authorization, cancellation and expiry. A `202` is not completed work.
- If a retry can exceed the caller's deadline, do not retry synchronously. Bound queue wait, processing time and attempts; cancel abandoned work when safe. A smaller timeout does not itself make an unavailable system reliable.
- If availability depends on a shared single instance that cannot meet the target, record the topology gap. Cache, asynchronous code or another language cannot invent failover, durable secret storage or tested restoration.
- Select PostgreSQL backup/restore mechanisms against RPO/RTO; SQL dumps, filesystem-level backups and continuous archiving have different procedures. Use only configured, tested mechanisms. See [PostgreSQL backup approaches](https://www.postgresql.org/docs/17/backup.html) and [operations](operations.md).

## 8. Worked choices and required evidence

| Application | Initial selection and explicit omissions | Evidence and trigger to change |
| --- | --- | --- |
| Public brochure with no runtime editing | Static artifact; no app database, bucket, cache or worker | Confirm no uploads/private data; reconsider on runtime content editing |
| Team CRUD dashboard | PostgreSQL + Casdoor + OpenBao; no Valkey initially | Authorized CRUD and realistic query/load results; cache only after an identified bottleneck |
| Private document portal | PostgreSQL ownership + S3 files + Casdoor + OpenBao | Cross-user access denied, size limits, interrupted upload and restore; add worker only for required processing |
| Public frequently read catalogue | Build artifact for publication-time content; PostgreSQL only when runtime editing or other authoritative mutable records require it. Add a shared cache only for a measured bottleneck with acceptable staleness | Confirm editing/freshness model first; for a selected cache, test cold/hot latency, invalidation and database survival during outage |
| Durable export button | PostgreSQL operation + S3 result; choose one job mechanism for independent exports | Duplicate request/crash/ack recovery; no Temporal unless additional process semantics exist |
| Purchase requiring approval then several external steps | PostgreSQL business state + Temporal; S3 only for actual files | Replay, duplicate external effects, declined approval, compensation and deployment compatibility |
| RAG search over private files | S3 originals + PostgreSQL/pgvector + APISIX + a justified ingestion worker | Tenant-filtered relevance, deletion, source revision, retry, query and ingestion SLOs; no Valkey corpus |
| Live status board | Authoritative state in PostgreSQL; optional Pub/Sub hint + refetch | Disconnect/reconnect recovers state; no promise that all notifications are delivered |

For every selected store, deliver: exact data ownership, used/not-used alternatives, credentials/permissions, expected volume and growth, retention/deletion, timeout and outage behavior, backup/rebuild procedure, tested evidence, unresolved assumptions, and a measurable reconsideration trigger. Record a test as planned until actually executed. Hand off implementation to the relevant contributor skill through [service-decisions](service-decisions.md).
