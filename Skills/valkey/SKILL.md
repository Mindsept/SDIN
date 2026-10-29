---
name: valkey
description: Decide whether an SDIN application needs Valkey and implement bounded cache, ephemeral shared state or competing Stream jobs, including optional RAG ingestion jobs. Use for app integration; corpus and vectors remain in S3 and PostgreSQL.
---

# Valkey in SDIN applications

## Decide before implementing

Describe the user-visible need, data lifetime and workload. Measure the direct path before adding cache; prefer direct bounded work when it meets the request SLO. Use Valkey for justified shared ephemeral state, caching or independent competing jobs. `Valkey: not used` is valid even with RAG; record evidence, simpler approach and revisit trigger. Long waits, durable timers, compensation and human decisions belong to the existing Temporal workflow skill when needed.

Select the use case separately: cache, rate/session state, notifications or Stream jobs. A cache integration does not create a worker, Stream or outbox. Reuse a compatible client and existing job mechanism. Bounded in-process caching may suffice for one process when independent values and restart loss are acceptable; shared correctness-sensitive state is a different requirement.

Set TTL from tolerated staleness, and bound key cardinality, value bytes and miss concurrency from the workload. For jobs, set admission, retained backlog, retry budget and concurrency from completion targets and downstream capacity. Use the relevant signals (hit/miss latency for cache, age/pending for jobs), not every metric for every use. Add distributed locking or extra workers only when local coalescing/backpressure cannot meet a demonstrated requirement.

## Platform contract

- Read `td/core-platform/README.md`, `podman-compose.yml`, app compose and worker code. Use the shared `redis://valkey.internal:6379` endpoint on `core-network`; `redis.internal` is a compatibility alias. Do not add another broker/cache container by default.
- Prefix keys, channels, consumer groups where shared, and Streams with `<app>:`; define a namespace per use case. Prefixes prevent accidental collisions but are not security isolation: this dev instance has no per-app ACL configured. End-user access must go through the authorized app API, not a browser connection to Valkey.
- PostgreSQL owns durable business state. Valkey's configured AOF does not make a cache/queue an authoritative business ledger or guarantee exactly-once effects. Document required persistence, retention and recovery for jobs.

## Design and implementation

1. Complete the need gate. Define a key schema, TTL, cardinality, payload size and concurrency bounds. User-specific cached results need user/tenant/authorization scope and a version; invalidate on relevant data or permissions changes. Recheck current access before returning a cached private result.
2. Validate cached/message payload schemas and versions; never use executable deserialization. Keep sensitive data minimal and credentials out. Bound fallback requests on outage or miss so the database is not overwhelmed; never bypass authorization or rate limits when Valkey fails.
3. For competing jobs, use a Stream consumer group. Persist durable job/business state, enqueue through an outbox when SQL-to-queue delivery must be reliable, and make each side effect idempotent. Ack only after durable completion. Claim abandoned pending entries with an explicit policy, cap retries and provide bounded poison-message handling.
4. For Streams, bound retention without trimming needed recovery data; configure worker concurrency, admission and graceful shutdown. Observe queue age/pending/retries for jobs, hit/miss latency for cache, and memory for either. Do not use KEYS or global FLUSH commands for normal app operations.
5. For RAG, first store original corpus documents in private S3. PostgreSQL stores document/version/ACL status, extracted chunks and pgvector embeddings from `task:embed`. Valkey carries only a document ID, source/pipeline version and job ID if async ingestion is justified. Workers recheck document status/rights, fetch the S3 object and commit derived state before acking. Stale jobs must not resurrect replaced/deleted documents.
6. For RAG retrieval, filter current document ACL/tenant and active corpus version in PostgreSQL before injecting context into the model prompt. Treat retrieved text as untrusted content, preserve source citations and bound retrieved tokens. Do not cache corpus results across authorization scopes or corpus versions.

Read the relevant [integration patterns](references/integration-patterns.md); its corpus pipeline applies only to RAG, not ordinary cache/queue work. Use [temporal-workflows](../temporal-workflows/SKILL.md) for durable orchestration requirements. Do not re-run architecture selection when the service decision is already established.

## Acceptance evidence

- Verify two users cannot share private cached results, permission changes revoke cached access, and malformed entries fail safely. Verify bounded behavior during Valkey outage and concurrent misses.
- For Streams, exercise repeated delivery, crash after a committed side effect but before ack, pending reclaim, poison jobs and shutdown. Assert one durable business effect, not one message delivery.
- For RAG, exercise duplicate ingestion, version replacement, deletion during processing, failed embedding and cross-tenant retrieval. State whether Valkey was selected and why; do not claim these live checks passed unless executed.
