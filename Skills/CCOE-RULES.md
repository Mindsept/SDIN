# CCoE rules: PostgreSQL, SeaweedFS/S3 and Valkey

Rules are stable identifiers so code review and audit reports can
refer to the same requirement. `MUST` is a blocking contract; `SHOULD` is the
default with an evidence-backed exception recorded in the app README.
Service-specific rules apply only when that service is selected; record a
justified N/A for non-use. The service-need gate always applies.

## 0. Simplicity

- **R-0-01 — MUST:** Before adding PostgreSQL, S3 or Valkey, state the
  user-facing need, compare the direct/no-service path and existing services,
  then choose the least complex option that meets it. Explicitly allow
  `not used`; record the choice and a revisit trigger in the app README. **Why:**
  every dependency adds code, state, failure modes and operational work.
  **Compute avoided:** unused containers, network hops, cache invalidation,
  duplicate storage and provisioning/build work.

## 1. PostgreSQL

- **R-1-01 — MUST:** Use the app's provisioned database and user, with the
  connection secret at `secret/<app>/postgres`; never use the shared `postgres`
  superuser from app runtime code. **Why:** database/user isolation limits
  blast radius and makes ownership clear. **Compute avoided:** duplicate
  database instances and repeated privilege troubleshooting.
- **R-1-02 — MUST:** Keep durable structured business records in PostgreSQL;
  model relationships and constraints in the schema. Store large binary
  payloads in S3 and keep their object key plus metadata in PostgreSQL. **Why:**
  relational constraints protect consistency while object storage is better
  suited to large blobs. **Compute avoided:** scanning blob-heavy tables,
  oversized database backups and duplicated blob transfer through SQL.
- **R-1-03 — MUST:** Ship schema changes as ordered, repeatable migrations;
  do not mutate production schema during ordinary request handling. **Why:**
  deploys need a reviewable and recoverable schema history. **Compute avoided:**
  emergency full restores and repeated manual schema repair.
- **R-1-04 — MUST:** Parameterize values in SQL; do not concatenate user input
  into SQL text. **Why:** parameters separate data from executable syntax.
  **Compute avoided:** incident response and reprocessing after injection.
- **R-1-05 — SHOULD:** Select only needed columns, paginate unbounded results,
  and add indexes in response to measured query patterns. **Why:** bounded
  work keeps latency and resource use predictable. **Compute avoided:** table
  scans, excess data transfer and indexes that consume storage/write I/O without
  helping a query.
- **R-1-06 — MUST:** Keep credentials out of source, images and logs; load them
  at runtime from the app's OpenBao path. **Why:** credentials can be rotated
  without rebuilding artifacts. **Compute avoided:** image rebuilds and
  incident-driven credential-wide rotations.
- **R-1-07 — MUST:** Authorize every user-facing read, update and delete against
  the authenticated actor and the record's owner/tenant on the server. A client
  supplied ID is a selector, never proof of access. **Why:** users of one app
  may be mutually untrusted. **Compute avoided:** breach response, data
  restoration and support work caused by cross-tenant exposure.
- **R-1-08 — MUST:** Test allowed access and denied cross-user/tenant access for
  critical data operations, including unauthenticated and role-boundary cases.
  **Why:** happy-path tests do not detect insecure direct object references.
  **Compute avoided:** incident investigation and recovery after data leaks.
- **R-1-09 — MUST:** Minimize sensitive data and define retention/erasure across
  the database and derived stores. **Why:** copies persist beyond the original
  row unless deliberately removed. **Compute avoided:** unnecessary backups,
  cache invalidations at scale and manual erasure work.

## 2. SeaweedFS / S3

- **R-2-01 — MUST:** Use the app's bucket and bucket-scoped identity from
  `secret/<app>/objectstore`; applications must not use platform-admin or a
  credential shared across apps. **Why:** scoped access contains compromise
  and accidental deletion. **Compute avoided:** cross-app recovery and
  re-provisioning after credential leakage.
- **R-2-02 — MUST:** Treat S3 as object storage, not a filesystem or relational
  database. Persist object bytes through the S3 API and store object keys,
  ownership and business metadata in the selected durable persistence layer
  (PostgreSQL for this platform's RAG). **Why:** S3 object operations
  and SQL transactions have different consistency boundaries. **Compute
  avoided:** blob scans, repeated transfer and custom synchronization logic.
- **R-2-03 — MUST:** Keep a bucket private by default. Public read requires the
  app's explicit `PUBLIC_BUCKET=1` choice and must be limited to that bucket.
  **Why:** anonymous access cannot enforce app-level authorization. **Compute
  avoided:** cleanup and re-upload after public data exposure.
- **R-2-04 — MUST:** Use the endpoint appropriate to the caller:
  `http://host.containers.internal:9000` from app containers and
  `http://localhost:9000` from the host. **Why:** the platform models S3 as an
  external/cloud-style service, not a `.internal` DNS service. **Compute
  avoided:** retry storms and debugging caused by unreachable endpoints.
- **R-2-05 — SHOULD:** Use deterministic, app-owned object key prefixes, set
  content type, and define lifecycle/retention behavior for generated or
  replaceable objects. **Why:** objects need traceable ownership and cleanup.
  **Compute avoided:** orphan accumulation, redundant uploads and broad bucket
  listings.
- **R-2-06 — MUST:** Never log S3 secret keys, signed URLs or object contents;
  load keys from `secret/<app>/objectstore`. **Why:** logs are broadly visible
  and long-lived. **Compute avoided:** credential rotation and object
  re-publication work after a leak.
- **R-2-07 — MUST:** Authorize each upload/download/overwrite/delete against
  the owning PostgreSQL record before issuing access or a signed URL. **Why:**
  an opaque key is not authorization. **Compute avoided:** breach response and
  re-upload after private object exposure.
- **R-2-08 — MUST:** Bound upload size before buffering, validate actual content
  against an allowlist, and treat filenames/metadata as untrusted. **Why:**
  headers and extensions are user-controlled; unbounded content can exhaust
  memory or disk. **Compute avoided:** crash recovery, malware cleanup and
  oversized storage/transfer.
- **R-2-09 — MUST:** Define cleanup for replaced/deleted records and failed
  cross-service writes. **Why:** SQL and S3 do not commit atomically. **Compute
  avoided:** orphan scans, manual reconciliation and redundant stored objects.

## 3. Valkey

- **R-3-01 — MUST:** Prefix every application key, channel and stream with
  `<app>:` and give each use case its own key namespace. **Why:** the Valkey
  instance is shared. **Compute avoided:** collision debugging and recovery
  from one app overwriting another app's state.
- **R-3-02 — MUST:** Use Valkey for rebuildable cache/ephemeral state or
  recoverable asynchronous work; PostgreSQL remains the source of truth for
  durable business data. **Why:** cache eviction/restart must not erase the
  system of record. **Compute avoided:** reconstructing authoritative data from
  logs or backups after cache loss.
- **R-3-03 — MUST:** Every cache entry has an explicit TTL unless the design
  documents why it must live for the process lifetime and how it is bounded.
  **Why:** shared memory is finite. **Compute avoided:** memory growth, eviction
  churn and oversized Valkey instances.
- **R-3-04 — MUST:** Use Streams with consumer groups only for independent,
  competing work that can be retried and whose delivery is idempotent. Ack only
  after durable completion; handle pending entries and poison messages.
  **Why:** delivery can repeat after a crash. **Compute avoided:** duplicate
  side effects, unbounded retries and manual queue recovery.
- **R-3-05 — MUST:** Use Temporal rather than a Valkey Stream when a workflow
  requires durable long waits, timers, multi-step retries, compensation
  or human approval. **Why:** Streams are work queues, not durable workflow
  history. **Compute avoided:** polling workers kept alive during waits and
  custom replay/orchestration code.
- **R-3-06 — MUST:** Use `redis://valkey.internal:6379` from app containers and
  load any app credentials from OpenBao if the platform contract changes; do
  not add a separate Valkey container for an ordinary app. **Why:** the shared
  service is the platform contract. **Compute avoided:** underused duplicate
  instances and their monitoring/backup overhead.
- **R-3-07 — MUST:** Include user/tenant/role scope in cached user-specific
  results; re-authorize against current state before acting on queued work.
  **Why:** cache keys and queue payloads are not authorization decisions.
  **Compute avoided:** data-leak incident response and replay of unauthorized
  side effects.
- **R-3-08 — MUST:** Bound fallback load, retries, queue growth and per-user
  concurrency. **Why:** an outage or abusive client can otherwise amplify load
  on shared Valkey and PostgreSQL. **Compute avoided:** cascading overload and
  emergency capacity increases.
- **R-3-09 — MUST:** For RAG ingestion, keep original corpus objects in the app's
  S3 bucket and chunks/embeddings in its PostgreSQL/pgvector database; use
  Valkey only for a small document/version job reference when asynchronous
  workers are justified. Never place documents, chunks or vectors in Valkey.
  **Why:** Valkey is shared ephemeral state, not durable corpus storage.
  **Compute avoided:** duplicate corpus storage, memory pressure, re-embedding
  after cache loss and a separate vector service.

## 4. Cross-service consistency

- **R-4-01 — MUST:** Do not imply a transaction spans PostgreSQL, S3 and
  Valkey. Persist a durable operation state in PostgreSQL and make external
  writes retryable/idempotent; use an outbox when database changes must reliably
  enqueue work. **Why:** there is no shared transaction coordinator in this
  platform. **Compute avoided:** reconciliation loops over inconsistent
  cross-service state and full data rebuilds.
- **R-4-02 — SHOULD:** Record the selected service, data owner, retention,
  recovery behavior and expected request/volume profile in the app README.
  **Why:** reviewers can test whether the dependency is warranted. **Compute
  avoided:** provisioning and operating unused capabilities.
- **R-4-03 — MUST:** Review a concrete user journey for authorization, failure,
  retry, deletion and recovery behavior across services. **Why:** users observe
  the combined system, not an individual database call. **Compute avoided:**
  rework and incident handling caused by partial or inconsistent outcomes.
- **R-4-04 — MUST:** Record each service decision in a small service-use table:
  user need, choice (`used`/`not used`), simpler alternatives considered,
  evidence/assumption and revisit trigger. **Why:** an agent must not infer that
  every available platform service is mandatory. **Compute avoided:** unused
  service clients, credentials, schemas, infrastructure and runtime calls.
