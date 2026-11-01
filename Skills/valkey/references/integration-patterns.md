# Valkey agent guide

Use these patterns when designing, implementing, reviewing or debugging cache,
ephemeral coordination, pub/sub or asynchronous work. Use the platform sources named in the skill entrypoint for current configuration.
Assume multiple users can trigger requests concurrently and maliciously; a
cache hit or queue message must never bypass application authorization.

## Platform contract

- From app containers connect to `redis://valkey.internal:6379`. The Redis
  protocol alias is retained, but the shared service is Valkey.
- The instance is shared. Every app key, channel and stream begins with
  `<app>:` and each use case gets its own namespace.
- PostgreSQL remains the source of truth for durable business data. Valkey is
  for rebuildable/ephemeral state and explicitly recoverable queued work.
- Streams with consumer groups suit independent competing work. Temporal is
  the platform choice for long waits, durable timers, step retries,
  compensation and human approval.

## Gate 0: is Valkey needed?

Before adding Valkey code, identify the user-visible need and data lifetime.
Consider no cache first: measure the direct path and add caching only when
latency/load evidence or a clear burst-protection need warrants invalidation
complexity. Consider no queue when work is synchronous, short and fits the
request SLO. Use PostgreSQL for durable business facts; use Valkey only when
ephemeral shared state, a measured high-read cache, pub/sub or competing
asynchronous work is actually needed. For durable long-running workflows,
assess Temporal instead of building queue semantics by hand.

If Valkey is not needed, do not add a client, connection setting, key schema,
container or queue. Record `Valkey: not used` in the app README, why the direct
path is sufficient, and evidence or a trigger that would justify revisiting
(for example, measured p99 or load exceeding the documented budget). Non-use is
a valid outcome; an unused cache adds invalidation work and failure modes.

## Cache-only integration

Read/authorize through the existing app boundary; try the scoped cache, then the
authoritative read on miss, and refill with an explicit TTL. Write through the
authoritative store first, then invalidate/update the relevant cache. Decide how
to tolerate or prevent stale repopulation racing with a concurrent write.

Set value and expiry in one command, for example the Redis-protocol shape
`SET <app>:<scope>:<resource>:<version> <serialized-value> EX <ttl-seconds>`.
The angle-bracket fields are inputs, not a command to execute. A separate SET then
EXPIRE can leave an immortal entry after a crash; SET without expiry also removes
an existing TTL. Use the client/version's supported options, not copied API syntax.
[Valkey SET](https://valkey.io/commands/set/).

Keep fallback and concurrent fills bounded. A small optional cache does not need
a distributed lock, Stream or job database. Re-authorize private cached results;
a TTL never guarantees timely permission revocation.

## RAG corpus ingestion: Valkey's narrow role

For a RAG corpus, Valkey is not the corpus store and is not the vector store.
Follow the platform's existing RAG path:

1. Upload the original document to the app's private SeaweedFS/S3 bucket first.
   Keep its opaque object key, owner/tenant, content hash, source version and
   ingestion status in the app's PostgreSQL database.
2. Extract and normalize text from that stored object, split it into bounded
   chunks, and generate embeddings through the platform LLM gateway's
   `task:embed` alias. The course/platform design uses pgvector in the app's
   existing PostgreSQL database; enable the `vector` extension only for this
   actual RAG use. Do not add another vector database.
3. Persist chunk text (or a justified minimized representation), source
   document/version, access scope and embedding in PostgreSQL. At retrieval,
   apply owner/tenant/document ACL filters in the vector query before results
   enter the prompt; similarity alone never authorizes a chunk.
4. Only if ingestion is too slow or bursty for the request SLO, enqueue a small
   Valkey Stream message containing document ID + version + job
   ID on an app-prefixed Stream. Never put the document, extracted corpus, chunk text, embeddings,
   credentials or user-supplied instructions in the message. The worker fetches
   the authorized source object from S3 and re-reads current ownership/status
   from PostgreSQL before processing.
5. Keep job state and completion durable in PostgreSQL. Use an outbox when a
   committed upload must reliably enqueue ingestion. Make work idempotent on
   `(document_id, source_version, pipeline_version)`; acknowledge the Stream
   entry only after chunks/vectors and durable status are committed. Bound
   retries and dead-letter retention.
6. On replacement or deletion, invalidate the previous document version and
   remove its chunks/vectors; retries for stale versions must not restore them.
   Keep the raw source object in S3 according to the corpus retention policy.

Do not add Valkey automatically for RAG. A small corpus that can be ingested
within the request SLO can use a direct path. Use Valkey only when measured
latency/volume requires decoupled competing workers. For long waits, durable
timers, multi-step retries or human review, use Temporal rather than stretching
a Stream into a workflow engine.

## Agent workflow

1. Complete Gate 0 and record the service decision before implementation.
2. State the data's role: cache, ephemeral coordination, pub/sub notification
   or work queue. If loss on restart is unacceptable, do not keep the only
   durable copy in Valkey.
3. Prefix every key/channel/stream with `<app>:`. For cached user/tenant-scoped
   results, include authorization scope and relevant data version in the key.
   Never cache a response so broadly that one user's result can be served to
   another user.
4. Bound cardinality and memory; give cache entries explicit TTLs.
5. Treat cached values as untrusted serialized input: validate schema/version,
   avoid executable serialization formats, and do not cache credentials or
   sensitive data unless necessary and protected. On cache miss or Valkey
   outage, use a bounded fallback; do not cause a database stampede.
6. For Streams, use a consumer group when workers compete. Make handlers
   idempotent, ack only after durable completion, and define retry,
   pending-entry and poison-message handling.
7. Validate and authorize work at execution time too; queue payloads may be
   stale, duplicated or malformed. Keep payloads minimal (usually durable row
   IDs, not secrets or whole user records) and re-check current ownership/state
   before applying side effects.
8. If a PostgreSQL transaction must reliably enqueue work, use a transactional
   outbox. A database commit and Valkey publish are not atomic together.
9. Use Temporal instead of Streams for workflows that must survive restarts
   across long waits or require durable timers, retries or compensation.
10. Apply per-user or per-tenant rate/concurrency limits at the app boundary;
   a shared Valkey namespace is not itself an authorization boundary. Bound
   retries and dead-letter retention so abusive or poison work cannot grow
   without limit.
11. Measure hit rate, queue age, pending count, processing duration and memory
    before changing eviction policy or adding infrastructure.

## Reject or challenge

- Unprefixed keys, unbounded key growth or cache entries with no expiry/bound.
- Durable business state stored only in Valkey.
- Cache keys that omit user/tenant/role/version when the value is user-scoped.
- Treating key secrecy as authorization or trusting job payloads without
  revalidating current actor/record policy.
- Treating pub/sub as durable delivery or acknowledging a Stream entry before
  work is durably complete.
- Unlimited retries, unbounded streams or fallback logic that overloads
  PostgreSQL during a Valkey outage.
- Using Streams to simulate a multi-day workflow or adding another cache/broker
  without measured need.
- Putting original documents, extracted corpus, chunks or vectors in Valkey.
- Queuing an object key without an app prefix, durable document record, or
  worker-side authorization/version check.

Explain the reason and compute/operations avoided for each pattern. Configuration review cannot prove call-level TTLs, delivery guarantees or idempotency; cover
those with integration tests and review.
