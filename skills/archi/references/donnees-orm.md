# Data, ORMs, transactions and access cost

Reference for the `archi` skill. Read when the application persists, queries, indexes or synchronizes data. For controller/service/domain/adapter separation, see [Code structures](structures-code.md). An application without persistence does not need to adopt an ORM, database or repository.

**Status:** proposed design rules, distinct from contracts already present in SDI. Recommendations are conditional on the need and existing system. External sources are official documentation and repositories, consulted on **October 14, 2026**; check the capabilities of the version locked in the project before any implementation. No benchmark, improvement percentage or absolute ORM ranking is assumed.

## Contents

1. [SDI platform storage contracts](#1-sdi-platform-storage-contracts)
2. [Choosing an ORM, query builder or SQL](#2-choosing-an-orm-query-builder-or-sql)
3. [Choices by ecosystem](#3-choices-by-ecosystem)
4. [Transactions and concurrency](#4-transactions-and-concurrency)
5. [Migrations and schema ownership](#5-migrations-and-schema-ownership)
6. [Queries, indexes and pagination](#6-queries-indexes-and-pagination)
7. [Pools, budgets and asynchronous execution](#7-pools-budgets-and-asynchronous-execution)
8. [Recovery, idempotence and outbox](#8-recovery-idempotence-and-outbox)
9. [Tenant isolation and permissions](#9-tenant-isolation-and-permissions)
10. [RAG and pgvector](#10-rag-and-pgvector)
11. [Verification and expected decisions](#11-verification-and-expected-decisions)

## 1. SDI platform storage contracts

These elements are observed in repository files, not validated on a running installation.

| Component | Provided contract | Consequence for the app |
|---|---|---|
| Postgres | Shared instance, one DB and user per app; `postgres.internal:5432` on the container side | The app bootstrap creates its resources; its migrations manage its schema. A shared instance implies a global connection and I/O budget |
| pgvector | Extension library present in the Postgres image; activation in each DB on demand | No separate vector database by default; no supplied RAG pipeline. Plan extension activation and useful migrations |
| OpenBao | Secrets under `secret/<app>/…`, including `postgres` and `objectstore` | Read at backend component startup; no DB password or S3 key in a browser bundle |
| S3 / SeaweedFS | Service modeled as external, one bucket and restricted key per app; backend: `host.containers.internal:9000`, host/browser: `localhost:9000` | Files in S3, metadata/references in Postgres. No common atomic Postgres/S3 transaction is provided |
| Valkey | Shared service, keys prefixed with `<app>:`; cache, pub/sub and Streams | Define TTL, capacity, acknowledgment/recovery according to use. A prefix is a naming convention, not strong authorization by itself |
| Temporal | One namespace per app; server at `temporal.internal:7233`; technical persistence in the `temporal` and `temporal_visibility` DBs of shared Postgres | The app uses the Temporal SDK/API; it does not modify the engine's internal tables. Its business state remains in its own schema |

Local sources: [README, lines 18–35 and 251–297](../../../td/core-platform/README.md), [compose, lines 156–166](../../../td/core-platform/podman-compose.yml), [app bootstrap, lines 200–218 and 239–266](../../../td/core-platform/templates/bootstrap.sh). The generic bootstrap does not systematically activate `vector`.

Casdoor and Umami also have data in the shared Postgres instance; their schemas remain under their own ownership. The Postgres budget therefore cannot be calculated solely from the app's API containers.

**DATA-01 — MUST:** assign a source of truth and an owner to each data category; distinguish business data, S3 objects, cache, messages and orchestration history. **Benefit:** understandable correction, retention and recovery. **Compute avoided:** synchronization and dual writes without a defined use; accepted cost: explicit references and possibly reconciliation between systems.

**DATA-02 — SHOULD:** first use existing capabilities suited to the need, notably Postgres and pgvector for RAG reasonably served by this database, before introducing a new engine. **Benefit:** simpler operations and consistency. **Compute avoided:** processes, replication, indexing and backup of additional storage; accepted cost: sharing Postgres resources and measuring when this solution becomes insufficient.

### Illustrative document model

```text
Postgres : documents(id, tenant_id, object_key, content_hash, status, version…)
S3       : document content, associated with object_key
Valkey   : indexing message with document_id and version, if asynchronous
Postgres : chunks(document_id, version, ordinal, text, embedding…)
Temporal : technical state of an approval process, if durable
```

This schema illustrates a possible application; it does not describe any already-delivered table. Avoid base64 files in a column merely to bypass S3 management. Conversely, small transactional contents may be stored in SQL if size, access and retention justify it: the data type decides, not a generic prohibition.

## 2. Choosing an ORM, query builder or SQL

**DATA-03 — MUST:** choose the access tool based on queries, transactions, existing conventions and team skills; document its migration owner and pooling mode. **Benefit:** an actionable decision. **Compute avoided:** competing dependencies, duplicate migrations and speculative rewrites; accepted cost: a brief evaluation of a few representative queries.

**DATA-04 — MUST:** keep SQL, ORM and data SDKs in identifiable adapters/repositories, with parameterized queries and an explicit output contract. **Benefit:** controllers independent of storage and protection against value injection. **Compute avoided:** accidental loading at the transport layer and reconstruction of unnecessary graphs; accepted cost: mapping/projection at the boundary. Dynamic table names, column names or sort directions cannot be secured with a simple value parameter: use a closed allowlist or the builder's safe mechanism.

“Adapter/repository” describes a responsibility here, not a mandatory class: a named selector/query function or a persistence function in a Phoenix context is sufficient if the use case explicitly delegates access to it and invariants remain separate. Several functions may share a coherent module; do not copy an ORM's entire API into an empty interface. This idiomatic mapping does not allow queries directly in the controller or scattered throughout business orchestration. See the variants in [structures-code](structures-code.md).

| Option | Prefer when | Cost and risk to handle | Expected evidence |
|---|---|---|---|
| Framework-integrated ORM | Relational CRUD, established conventions, useful models and migrations | Implicit loading, change tracking, hooks, generated queries | SQL inspected on critical journeys; transaction and query count understood |
| Typed query builder | Composable queries, many projections and a need for explicit SQL | Schema/types and migrations to maintain; SQL semantics still required | Typed projections, parameterized filters and identified migration ownership |
| Direct parameterized SQL | Postgres-specific query, bulk import, fine control of a plan, SQL-proficient team | Mapping, possible generation, limited portability, query maintenance | Tests with the real engine and a representative query plan |
| SQL generating typed code | SQL as a readable source and static access checking | Generation step, code/schema synchronization, dialect coverage | Reproducible generation, no manual modification of generated code |
| Targeted combination | ORM useful day to day but a specific read/write requires SQL | Two access APIs, transaction/session sharing to control | Precise boundary and the same schema owner; no accidental extra pool |

An ORM is neither automatically slow nor a substitute for knowing how to read SQL. Direct SQL is not automatically performant: a bad index or wrong cardinality remains a problem. Do not replace the entire access layer to optimize an isolated query. A local measurement distinguishes SQL time, network time, pool wait, materialization and serialization.

### Short decision guide

1. Inventory five to ten representative operations if the product is sufficiently rich: filtered lists, transactional writes, imports, aggregations, search, access rights.
2. Examine the existing tool; continuity has value unless a limitation is demonstrated.
3. For the target engine, verify useful types, transactions, cancellation, migrations, driver limits and generated code.
4. Choose a primary mechanism. Add a localized SQL exception if it genuinely improves clarity or the plan.
5. Record what the choice does not cover: for example no automatic relationship loading, no generated migration, synchronous driver.

This operation count is a guide for a substantial product, not a minimum to invent for a small app.

## 3. Choices by ecosystem

The links in each row are official sources consulted on October 14, 2026. The “guidance” column is advice from the skill; the documentation describes capabilities, not a performance ranking.

| Language / context | Choices and guidance | Migrations and pitfalls |
|---|---|---|
| Python / Django | [Django ORM](https://docs.djangoproject.com/en/5.2/topics/db/queries/) to stay within framework conventions; specific reads in selectors/repositories, targeted SQL if necessary | Django migrations own the schema. Watch deferred QuerySet evaluation, `select_related`/`prefetch_related` and sync/async boundaries |
| Python / API outside Django | [SQLAlchemy ORM/Core](https://docs.sqlalchemy.org/en/20/intro.html) according to the need for mapping or SQL expressions; ORM for persistent objects, Core for explicit access | [Alembic](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) for migrations. Autogeneration produces proposals to review; bounded session and transaction scope |
| TypeScript / schema and generated client | [Prisma](https://www.prisma.io/docs/orm) if its schema model and client suit the team | Prisma Migrate if selected; examine the driver/adapter for the project's version, since pool configuration and execution engine vary |
| TypeScript / SQL approach | [Drizzle](https://orm.drizzle.team/docs/overview) provides SQL and relational APIs; useful for keeping schema and queries close to SQL | Drizzle Kit or an explicitly owned SQL migration process; check the queries actually emitted rather than inferring their cost from the API type |
| TypeScript / query builder | [Kysely](https://kysely.dev/) for composed, typed SQL queries without imposing an entity model with change tracking | Kysely migrations or another single pipeline; define the source of DB types and their synchronization |
| Java/Kotlin / persistent objects | JPA with [Hibernate](https://docs.hibernate.org/orm/current/userguide/html_single/) if this model is useful or already present | Flyway/Liquibase or another project-selected pipeline; no automatic schema update in production. Watch fetch plans, lazy loading and persistence context |
| Java/Kotlin / explicit SQL | [jOOQ](https://www.jooq.org/doc/latest/manual/sql-execution/) for a DSL/generated code; JDBC for direct SQL and explicit control | Same migration owner as the rest of the app; check compatibility/license of the selected edition and engine without assuming all editions are equivalent |
| Go / SQL first | [sqlc](https://github.com/sqlc-dev/sqlc) generates typed code from SQL; [pgx/pgxpool](https://pkg.go.dev/github.com/jackc/pgx/v5/pgxpool) provides Postgres access and pooling | SQL migration tool selected separately; sqlc generation alone does not constitute a schema deployment policy |
| Go / ORM | [GORM](https://gorm.io/docs/) if its conventions and associations simplify the product | Control preloading and SQL. Available automatic migration is not a sufficient strategy for risky production changes |
| C# / tracked model | [EF Core](https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying) for useful mapping, LINQ and tracking; projections and no-tracking reads when appropriate | EF Core migrations if it owns the schema; bounded `DbContext` lifetime; inspect queries and N+1 |
| C# / explicit SQL | [Dapper](https://github.com/DapperLib/Dapper) for SQL and lightweight mapping, notably specific reads | Does not provide the same tracking model as EF; choose migration ownership and explicitly share connection/transaction when combining them |
| Rust / typed DSL | [Diesel](https://diesel.rs/guides/getting-started) if its schema, DSL and checks fit | Diesel migrations if it owns the schema; check the driver execution mode and selected async integration; do not block an async executor with a synchronous connection |
| Rust / SQL and async | [SQLx](https://github.com/transact-rs/sqlx) for async SQL access and query checking through its tooling when configured | SQLx migrations or a single pipeline; checked macros require a metadata/build-database strategy, unlike dynamic queries |
| PHP / Symfony | [Doctrine ORM/DBAL](https://www.doctrine-project.org/projects/doctrine-orm/en/current/tutorials/getting-started.html) for mapping or explicit SQL as needed | Doctrine Migrations if it owns the schema; watch unit of work, flush, proxies and memory during batches |
| PHP / Laravel | [Eloquent](https://laravel.com/docs/12.x/eloquent) and the framework's query builder for consistency with the existing system | Laravel migrations; avoid orchestration hidden in observers and relationships loaded in a loop |
| Ruby / Rails | [Active Record](https://guides.rubyonrails.org/active_record_basics.html) when Rails is chosen; query objects for specific reads | Rails migrations; `includes`/`preload` according to expected SQL, explicit callbacks, bounded batch processing |
| Elixir / Phoenix | [Ecto](https://ecto.hexdocs.pm/Ecto.html): schemas, changesets, queries and Repo; `Ecto.Multi` to compose transactional operations where appropriate | Ecto migrations; distinguish changeset validation, DB constraints and business policy; do not make an external call inside a long transaction |

There is no need to install all these tools. For an existing SDI Bun app, first examine its runtime, PostgreSQL driver and dependencies; the availability of an ORM in the Node ecosystem alone does not prove compatibility of all its features with the chosen runtime.

## 4. Transactions and concurrency

**DATA-05 — MUST:** define a transactional unit for each atomic business change and have all its SQL accesses share the same transaction. **Benefit:** invariants survive an intermediate error. **Compute avoided:** repairs, rereads and compensation for partial changes; accepted cost: connections and locks held for a controlled duration.

**DATA-06 — MUST:** keep transactions short and do not wait inside them for a user response, an LLM, an S3 upload or other network activity not necessary for the SQL decision. **Benefit:** fewer locks and blocked operations. **Compute avoided:** queues, occupied connections and retries caused by contention; accepted cost: intermediate states and explicit coordination of external effects.

**DATA-07 — MUST:** protect concurrency invariants with appropriate constraints and mechanisms rather than an uncontrolled “read then write”. **Benefit:** no duplicates or lost transitions under load. **Compute avoided:** duplicate processing and reconciliation; accepted cost: unique indexes, locks or retry attempts.

| Problem | Candidate mechanism | Decision point |
|---|---|---|
| Unique business identifier | Unique constraint, possibly combined with tenant | Handle the DB conflict as an expected outcome; a preliminary check does not eliminate a race |
| Concurrent modification of a case | Optimistic version in `UPDATE ... WHERE version = ...` | Zero modified rows signal a conflict; decide whether to reload, abort or retry |
| Resource that must be reserved once | Conditional atomic update or explicit lock in a transaction | Measure contention; do not lock more rows than necessary |
| Invariant across several rows | Appropriate isolation and locking, possibly serializable | Identify prevented anomalies and handle serialization errors |
| Independent batch | Transactions per bounded batch | Size based on memory, time and recovery; not one transaction spanning several hours |

The transaction is initiated in the use case or a unit of work it controls; the repository receives the appropriate context. A repository that systematically opens its own transaction prevents atomic orchestration across several writes.

Conceptual example, independent of the ORM:

```text
approveCase(actor, caseId, expectedVersion):
  within a transaction:
    read the case and its authorization scope
    check permission and the business transition
    update with a version check
    insert an outbox event if the external effect must be reliable
  return the validated result
```

Do not calculate a sensitive permission from a stale version if the transaction modifies the state it depends on. SQL constraints complement application validation: foreign keys, uniqueness, `NOT NULL` and `CHECK` express invariants that several write paths must respect.

## 5. Migrations and schema ownership

**DATA-08 — MUST:** choose a single owner and ordered migration history for each application schema, shared by the API and its workers. **Benefit:** deterministic deployment. **Compute avoided:** concurrent attempts, drift and resource recreation; accepted cost: a separate migration job or a clearly controlled exclusive mechanism. Casdoor, Umami and Temporal migrations remain under their respective tools.

**DATA-09 — MUST:** review generated SQL and test evolution from an already-deployed state, not just an empty database. **Benefit:** preserved data and anticipated locks. **Compute avoided:** accidental restores and backfills; accepted cost: upgrade testing with representative data and examination of the migration execution plan. Alembic itself states that autogenerated migrations are candidates to review: [official documentation](https://alembic.sqlalchemy.org/en/latest/autogenerate.html), consulted on October 14, 2026.

**DATA-10 — SHOULD:** use evolution through several compatible steps when old and new instances coexist: add, bounded backfill, switch reads/writes, then delayed removal. **Benefit:** application-level reversible deployment. **Compute avoided:** downtime and large-scale recovery; accepted cost: temporary compatibility, additional space and sometimes controlled dual writes.

Single ownership concerns modification authority, not necessarily a single developer. Migrations may be written by several teams but are consolidated into one chain applied once per environment.

Decide before deployment:

- Role with DDL privileges; runtime role limited to necessary operations.
- Exclusive execution and handling of migration timeouts/locks.
- API/worker compatibility during a rolling deployment.
- Estimated and observable backfill duration; cursor- or range-based recovery.
- Handling of indexes, constraints and extensions; operation order.
- Possible application rollback, corrective migration or tested restore; a destructive migration does not become reversible merely because a `down` function exists.

For Postgres, an index built with `CONCURRENTLY` has restrictions, including the absence of a conventional encompassing transaction; an interrupted build may leave an invalid index. Choose this option according to availability needs and verify the result. Source: [PostgreSQL, CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html), consulted on October 14, 2026; confirm the behavior of the instance version, configured here by the repository's image.

## 6. Queries, indexes and pagination

**DATA-11 — MUST:** bound results, select necessary columns and make query counts visible on critical journeys. **Benefit:** predictable latency and memory. **Compute avoided:** unnecessary scans/hydration, N+1 and serialization of large graphs; accepted cost: explicit projections and pagination.

**DATA-12 — SHOULD:** add or change indexes based on actually observed filters, joins, sorts and plans, accounting for write cost. **Benefit:** targeted optimization. **Compute avoided:** unnecessary page reads; accepted cost: space, index maintenance, write I/O and analysis after change. No index is free, and “index every column” is not a strategy.

### Avoid N+1 without loading everything

A list of N documents that triggers an owner read per document performs N additional queries. Choose as appropriate: join/projection, explicit preloading, query by a set of identifiers, or a dedicated read model. Also check for N+1 in serializers, templates, GraphQL resolvers and computed properties.

The remedy is not to `eager load` every relationship: several joined collections may multiply rows and objects. A test with several parents and realistic cardinalities observes query counts and result size. The count is a signal, not a universal “one query only” threshold. [EF Core describes projections, bounded results, pagination and lazy-loading pitfalls](https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying), official documentation consulted on October 14, 2026; the analysis applies here as SQL reasoning without attributing EF APIs to other ORMs.

### Reading a plan

Examine filters, cardinality estimates, rows actually read, buffers, sorts, loops and joins. A sequential scan may be the right plan for a small table or a very large result. Update statistics when the distribution changes; test parameters must represent small and large tenants, not only a favorable value.

`EXPLAIN ANALYZE` **executes** the query; it is not a side-effect-free inspection for a write. Use a test copy or a method with controlled effects. A rollback does not necessarily neutralize every external or non-transactional effect. Source: [PostgreSQL, using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html), consulted on October 14, 2026.

### Choosing pagination

| Need | Reasonable choice | Conditions |
|---|---|---|
| Small administration list, arbitrary page access | Offset/limit may suffice | Deterministic order and maximum size; measure deep pages |
| Feed or large catalog traversed sequentially | Keyset/cursor | Stable order with a unique tiebreaker; index consistent with filter and sort |
| Export | Batch reads or bounded stream | Explicit deadline, backpressure, memory, snapshot/consistency and recovery |

Conceptual keyset example:

```sql
SELECT id, title, created_at
FROM documents
WHERE tenant_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT $4;
```

The cursor includes the sort components and is validated; the limit is capped. Adapt types, null values, collation and sort direction. A possible index starts with the tenant, then the sort columns; its value is verified against the plan and data. Keyset does not provide jumping to page 900 or an exact count for free. Updates to sort columns during traversal can create duplicates or omissions: choose consistency appropriate to the product.

## 7. Pools, budgets and asynchronous execution

**DATA-13 — MUST:** size pools using the maximum number of simultaneous processes and replicas, reserving headroom for platform services, migrations, monitoring and operations. **Benefit:** no connection exhaustion during scale-out. **Compute avoided:** connection storms, retries and added instances that worsen contention; accepted cost: a bounded waiting queue and explicit shared budget.

Working formula:

```text
Σ (max_replicas_i × processes_per_replica_i × pools_per_process_i × max_pool_i)
  + platform_connections + migrations + operations + headroom
  ≤ available_instance_connection_budget
```

The maximum includes rolling deployments, migration jobs, worker peaks and any separate read pools. Temporal, Casdoor and Umami services also consume connections. In SDI, several apps share the instance; the platform owner arbitrates the total. Available connections do not necessarily equal the raw `max_connections` value if a reserve is configured.

**Illustrative** example, not a recommended value: three API replicas, two processes each and a pool of eight connections represent up to 48 connections for the API alone. Adding two workers with six each represents twelve additional connections; neither platform databases nor deployment headroom are included. The right value depends on throughput, query duration and acceptable wait, not a universal per-CPU multiplier.

**DATA-14 — MUST:** configure acquisition, connection, query and transaction with consistent deadlines, and observe pool waits, timeouts and cancellation. **Benefit:** controlled degradation. **Compute avoided:** work continuing after client abandonment and accumulation of already-doomed requests; accepted cost: deadline propagation and explicit error handling.

**DATA-15 — MUST:** respect the concurrency model of the driver and session; no mutable transactional session arbitrarily shared between concurrent tasks. **Benefit:** consistency and no invalid concurrent access. **Compute avoided:** blocked event loops, threads added to compensate and recovery from avoidable errors; accepted cost: one session per unit of work and an explicit sync/async adapter.

### Runtime-specific pitfalls

- **Django:** the consulted 5.2 documentation exposes async ORM methods, but states that transactions do not yet work in async mode; it recommends an entire synchronous transactional function called through `sync_to_async`. Do not scatter a transaction across several isolated calls or disable async protection. The documentation also advises avoiding persistent connections through `CONN_MAX_AGE` in this mode and choosing appropriate pooling. Check again for another version. [Django source](https://docs.djangoproject.com/en/5.2/topics/async/), October 14, 2026.
- **FastAPI/Python:** an `async def` route directly executing a synchronous driver call blocks its loop. Choose coherent async I/O or a synchronous path with controlled execution. An ordinary utility call is not automatically offloaded to a thread because it is invoked from FastAPI. [FastAPI source](https://fastapi.tiangolo.com/async/), October 14, 2026.
- **SQLAlchemy:** `AsyncSession` represents mutable transactional state; a separate session is required per concurrent task. Lazy relationships may introduce implicit I/O that must be controlled. [Async documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html), consulted on October 14, 2026.
- **Java/.NET:** do not share an ORM session/`DbContext` between parallel tasks. An async transport abstraction does not make JDBC non-blocking. Connection-pool size and thread-pool size are two different limits. For EF: [DbContext lifetime and configuration](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/), consulted on October 14, 2026.
- **Rust:** SQLx provides async APIs; a synchronous Diesel connection requires an integration mode compatible with the runtime if the app is async. Offloading to a bounded thread pool does not create infinite SQL capacity. [SQLx](https://github.com/transact-rs/sqlx) and [Diesel](https://diesel.rs/guides/getting-started), consulted on October 14, 2026.
- **TypeScript:** retain a reused client/pool per process according to the driver's rules. For Prisma, configuration may depend on the driver adapter and client generation used; do not copy parameters from another version. [Prisma pool documentation](https://docs.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections/connection-pool), consulted on October 14, 2026 for the documented case, without imposing that version.

An external pooler may be appropriate if process counts or short-lived connections require it; it does not replace Postgres's load budget. Check its pooling mode, prepared statements, session variables and expected transactions before introducing it.

## 8. Recovery, idempotence and outbox

**DATA-16 — MUST:** bound retries, identify transient errors and repeat the correct unit of work with an appropriate deadline and retry delay. **Benefit:** safe recovery without an infinite loop. **Compute avoided:** load amplification and repetition of unrecoverable operations; accepted cost: idempotence management, jitter/backoff and observability of abandoned attempts.

A serialization error generally requires retrying the **entire transaction**, including the decisions that determined its writes. Repeating only the last statement preserves reasoning that has become invalid. A business conflict or invalid input does not become transient by adding a retry. Source: [PostgreSQL, handling serialization failures](https://www.postgresql.org/docs/current/mvcc-serialization-failure-handling.html), consulted on October 14, 2026.

### Operation identifier

An idempotency key is tied to an actor/tenant, operation type and content or fingerprint. Define:

- scope and retention duration;
- unique constraint preventing two concurrent executions;
- result returned when the operation is already complete;
- behavior if the same key is reused with different content;
- handling of an `in_progress` state left by an interruption;
- effect of expiration on repetition risk.

**DATA-17 — MUST:** make effects that may be replayed by the client, queue or workflow engine idempotent, or explicitly document and control their compensation. **Benefit:** an ambiguous timeout does not cause a second unwanted business action. **Compute avoided:** duplicate imports, AI generations and writes; accepted cost: storing identifiers/results and bounded cleanup.

### Two writes do not form a distributed transaction

```text
Postgres transaction: business state + outbox event
Commit
Relay: reads a portion of the outbox, publishes, records progress
Consumer: deduplicates, executes its effect, acknowledges according to its guarantee
```

**DATA-18 — SHOULD:** use an outbox when losing an event between SQL commit and external publication would have a business impact and no existing mechanism covers this guarantee. **Benefit:** durable publication intent alongside business state. **Compute avoided:** repair scans and inconsistent processing; accepted cost: table, relay, purge, retries and possible duplicates. Do not create an outbox for a loss-tolerant UI event without a justified need.

The outbox does not guarantee end-to-end “exactly once”. Publication may succeed while local marking fails: the consumer handles duplicates. Avoid an SQL transaction remaining open during a slow publication; prefer a reservation/batch or another documented protocol. A notification mechanism may reduce polling, but reliable recovery does not depend solely on a volatile signal.

### Postgres, S3, Valkey and Temporal

- **S3:** key reservation, upload, SQL finalization and then orphan-object cleanup form one possible protocol. States and expiration must be defined; the repository does not provide a ready-made protocol. Do not delete a referenced object before determining the recovery policy.
- **Valkey Streams:** decide when to acknowledge, how to recover pending messages, how many attempts, where to examine persistent failures and when to trim. Business status in SQL and acknowledgment are not atomic across the two systems. Pub/sub alone does not replace a durable queue.
- **Temporal:** the engine manages workflow history and recovery; activities producing external effects must support their retry policy. The app namespace does not authorize the app to modify Temporal's technical DBs. A workflow is not a Postgres transaction remaining open during human waiting.
- **Cache:** the key includes the relevant access scope, version and query parameters; TTL is a freshness choice. Define invalidation, cache failure and control of simultaneous computations for an expired entry.

These choices complement SDI contracts; they are not presented as already implemented. For implementation, also consult [Valkey Streams](https://valkey.io/topics/streams-intro/) and [Temporal, Activities](https://docs.temporal.io/activities), official documentation consulted on October 14, 2026.

## 9. Tenant isolation and permissions

A DB per **app** is not a DB per user tenant. The app name, Valkey prefix, bucket and Temporal namespace do not by themselves define business users' rights.

**DATA-19 — MUST:** derive tenant and actor from an authenticated and authorized context; include their scope in every relevant read/write, join, cache, export and vector search. **Benefit:** access consistent with the object and tenant. **Compute avoided:** reads and data transfers that ultimately must be rejected; accepted cost: filters, constraints and negative access tests. A `tenant_id` value sent by the browser is not proof of authorization.

**DATA-20 — MUST:** distinguish migration and runtime roles, and grant the latter only the privileges actually required. **Benefit:** an app bug does not automatically gain control of every schema. **Compute avoided:** no presumed performance gain; accepted cost: role management and reduced blast radius, which is the main benefit here.

Postgres row-level security can reinforce application filters if correctly deployed. Superusers and roles with `BYPASSRLS` bypass it; table owners normally bypass it too unless appropriately configured. A session tenant variable requires a safe pooling strategy and proper cleanup, or an appropriate transaction scope. Verify policies with the runtime role, not only the migration owner. Source: [PostgreSQL, Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html), consulted on October 14, 2026.

Useful tests: user from another tenant, object moved to another scope, relationship to a forbidden object, export, shared cache, search with no results, insertion with a forged tenant, worker replaying an old message after an authorization change. HTTP middleware alone covers neither jobs, migrations nor administration scripts.

## 10. RAG and pgvector

The repository installs pgvector capability and routes embeddings through APISIX; it supplies neither a corpus, chunking, search nor business evaluation. Local source: [compose, lines 161–166](../../../td/core-platform/podman-compose.yml) and [README, lines 332–400](../../../td/core-platform/README.md).

**DATA-21 — MUST:** version the embedding representation with the document, chunking, model and its dimension, and ensure access scope before building the context intended for the LLM. **Benefit:** consistent retrieval, traceability and preserved permissions. **Compute avoided:** incompatible embeddings, blind reindexing and unnecessary context tokens; accepted cost: metadata and planned migrations/reindexing.

**DATA-22 — SHOULD:** start with exact search and a representative test corpus when that meets the need; add an approximate index according to observed latency, volume and quality. **Benefit:** measured optimization. **Compute avoided:** large indexes and premature rebuilding; accepted cost: measuring recall and search time. HNSW and IVFFlat have distinct tradeoffs; neither is declared the winner without data. [Official pgvector documentation](https://github.com/pgvector/pgvector), consulted on October 14, 2026.

Decisions to make explicit:

- Dimension, distance, possible normalization and compatibility between the model used for indexing and querying.
- Chunk size and overlap according to documents, evaluated on useful answers rather than a supposedly universal constant.
- Chunk uniqueness per document/version/ordinal to avoid duplicate reindexing.
- Content fingerprint to avoid unchanged embedding calls; reuse across tenants respects confidentiality rules.
- Activation of `CREATE EXTENSION IF NOT EXISTS vector` by the authorized role in the relevant DBs; this is not a migration to execute on every request.
- Index and query consistent with the distance operator; test filter behavior with approximate search.
- Number of passages and context budget; document references retained for attribution.
- Deletion/archival: immediately remove or exclude forbidden chunks; clean vectors, objects and caches according to retention policy.
- Gradual reindexing after a model change, without mixing incompatible dimensions or vector spaces.

In the SDI routes analyzed, `task:embed` uses OpenAI even when the selected generation provider is Anthropic. The application goes through `llm.internal:9080`, with its virtual key and configured budget; it must not bypass this gateway for embeddings. This observation describes the repository, not a general comparison of provider offerings. No live call or RAG benchmark was performed to write this reference.

## 11. Verification and expected decisions

**DATA-23 — MUST:** test guarantees that depend on Postgres using Postgres and the relevant migrations rather than inferring them from an in-memory double or another engine. **Benefit:** verified constraints, transactions, dialect and permissions. **Compute avoided:** late investigations of engine differences; accepted cost: targeted integration tests, DB initialization and controlled cleanup.

**DATA-24 — SHOULD:** base optimization on observations of latency, pool waits, row volume, I/O, batch size and query count, without logging sensitive values. **Benefit:** the fix targets the actual cause. **Compute avoided:** cache or scale-out added to hide an expensive query; accepted cost: measured instrumentation, appropriate retention and sampling.

### Scenarios to select according to actual risks

| Guarantee | Useful test |
|---|---|
| Business transaction | Midway failure; no partial state remaining |
| Concurrency | Two actually simultaneous operations; expected uniqueness or conflict |
| Recovery | Interruption after commit before publication, or after effect before acknowledgment; single business result |
| Migrations | Upgrade from the previous version with data; compatibility of old readers and workers |
| N+1 / expensive query | Several parents and relationships, large and small tenants; SQL and plan observation |
| Pagination | Equal dates, limit, possible nulls, next page, defined concurrent modifications |
| Permissions | Wrong tenant, revoked permission, runtime DB role, export and vectors |
| Pool and async | Concurrency near the limit, expired acquisition, cancellation; no invalid shared session |
| S3 | Interrupted upload, missing reference, orphan object and replayed deletion |
| RAG | Question corpus with expectations and permissions, embedding-version change, deleted documents |

The expected output of a data-access decision includes: primary tool and possible exception, engine and contract, migration owner, transaction boundary, query/index/pagination strategy, connection budget, tenant/permissions, recovery of external effects and evidence obtained. If no DB is necessary, state that explicitly and do not invent the rest.
