---
name: postgresql
description: Decide whether an SDIN application needs PostgreSQL and implement its relational persistence, migrations, authorization, or pgvector RAG storage. Use when changing app data; do not invent a business app or schema for this platform repository.
---

# PostgreSQL in SDIN applications

## Decide before implementing

Identify the actual user journey, durability, concurrency, relationships and data volume. Compare no database, existing app persistence and PostgreSQL. Select the lightest option that preserves required durability and access guarantees. Browser or process memory is appropriate only when its lifetime and loss behavior meet the requirement. `PostgreSQL: not used` is a valid decision; document the reason, simpler alternative and revisit trigger in the app README's Structuring decisions section.

Reuse a justified selection; a column/query change does not reopen the whole architecture. For a small app, start with its existing database, one pool per process, ordinary tables and the indexes needed by actual queries. Do not add replicas, partitioning, a repository framework, cache or pgvector for ordinary CRUD.

Size the pool across **all** API/Worker replicas: the sum of their maxima must fit the allocated database connection budget, leaving capacity for migrations and shared services. Use measured query latency, lock waits and data growth to revisit it; more connections can worsen contention. Set a finite acquisition/query timeout and bounded result size. A basic migration needs a rollback/recovery decision, not automatically an online migration framework.

## Platform contract

- Read `td/core-platform/README.md`, `podman-compose.yml`, `templates/bootstrap.sh` and the target app. This repo provides a platform, not an implemented business application.
- Reuse `postgres.internal:5432` on `core-network`, with one app database and user. Bootstrap writes `secret/<app>/postgres`; retrieve credentials server-side at boot. Never expose a DSN/password in frontend code, images or logs, or run app requests as the platform superuser.
- The repository's current bootstrap provisions PostgreSQL and S3 unconditionally. If a service is not needed, adapt only the consuming app's copied bootstrap and compose/client configuration to skip it. Do not assume USE_POSTGRES or USE_OBJECTSTORE flags exist upstream.
- App-level database separation does not implement end-user authorization. Resolve identity server-side and constrain every record operation by its owner/tenant policy. Client IDs never grant access. The workshop's root credentials and plain transport are development configuration.

## Design and implementation

1. Complete the decision gate; identify data ownership, relational constraints, retention, deletion and recovery. Add migrations with explicit deploy compatibility and a reviewed recovery plan; never run DDL in ordinary requests.
2. Use bound query parameters. Dynamic identifiers/order clauses need a server-owned allowlist. Bound pagination, query duration and connection-pool size; select needed columns and justify indexes with actual access paths.
3. Enforce owner/tenant conditions on reads, writes and deletes, and database constraints for critical invariants. Use conditional updates/transactions to protect concurrent operations. Keep responses and logs free of credentials and unnecessary personal data.
4. Use SQL transactions for database changes. For external writes, make operation state and reconciliation explicit. Add an outbox only when a committed DB change must reliably trigger a message/effect; a single-database operation does not need one. Give repeatable side effects stable idempotency keys at their destination.
5. For an explicitly requested RAG feature, first store original documents in private S3. Enable pgvector in the app's existing DB only then; persist source/version metadata, chunks and embeddings generated via `task:embed`. Check model dimensions/version and rebuild deliberately on changes. Apply document/tenant ACL and active-version filters in retrieval before any chunk enters a prompt.

Read [integration patterns](references/integration-patterns.md) for data placement, access and deletion guidance. Read its RAG guidance only for a retrieval requirement; lexical search or a normal CRUD feature does not imply embeddings. Load the S3 and Valkey skills only when those dependencies are selected.

## Acceptance evidence

- Verify allowed and denied access with two users/tenants, unauthenticated requests, role changes and deleted records. Verify injection-shaped values remain values; test competing writes against the actual invariant.
- Verify migrations on an existing dataset, bounded list behavior and retry after a committed side effect. For RAG, verify private-document retrieval, version replacement and deletion of derived chunks/vectors.
- Record decisions, sensitive-data retention, critical paths and performance evidence in the app README. State which checks ran and which require the live platform; never claim integration success from a static inspection.
