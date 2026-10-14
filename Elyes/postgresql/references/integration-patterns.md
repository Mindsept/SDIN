# PostgreSQL agent guide

Use these patterns when designing, implementing, reviewing or debugging app-owned
relational persistence. Use the platform sources named in the skill entrypoint for current configuration.
Assume the application serves multiple real users, including mutually
untrusted users. A valid SQL query is not automatically an authorized query.

## Gate 0: is PostgreSQL needed?

Before adding PostgreSQL code, ask what user-visible capability requires
durable relational state. Consider no database first: static content, browser
state, or a bounded in-memory value may be enough for a prototype or
single-user tool. If the app already has a persistence layer, reuse it unless a
specific relational invariant cannot be met there. Use PostgreSQL when the
product needs durable shared records, relationships, constraints, concurrent
updates, search/filtering across records, or auditable ownership.

If it is not needed, do not provision a DB, create schema/migrations, or add a
database client. Record `PostgreSQL: not used` in the app README, the reason,
what simpler mechanism covers the need, and the trigger that would justify
revisiting the decision. Non-use is a valid and preferred outcome when it
meets the user need.

## Platform contract

- Connect to `postgres.internal:5432` from app containers.
- Each app gets one database and one user. Bootstrap publishes credentials at
  `secret/<app>/postgres`; never use the shared `postgres` superuser at runtime.
- PostgreSQL is shared with platform services and Temporal. Keep app data in
  its app-owned database; do not create another database server by default.
- The image includes pgvector. Enable the extension only when vector search is
  a real requirement for the app.

## Agent workflow

1. Complete Gate 0 and record the service decision before implementation.
2. Identify durable relational facts, relationships, ownership and deletion
   requirements before proposing tables.
3. Identify the actor and tenant/workspace for every user-facing read or write.
   Enforce ownership/tenant constraints in the server-side query or service
   layer; never trust a client-supplied user or tenant id as proof of access.
4. Put binary files and media in the app's S3 bucket; keep their stable object
   keys and business metadata in PostgreSQL.
   For RAG, keep the original corpus file in S3 and store extracted chunks,
   source/version/ACL metadata and embeddings in this app's PostgreSQL database
   with pgvector enabled only when needed. Call the platform `task:embed` alias
   for embeddings; do not add a separate vector database.
5. Add ordered schema migrations. Make compatibility explicit when deploys can
   overlap old and new app versions. Do not run DDL from request handlers.
6. Parameterize every value in SQL. Select only needed columns and bound list
   queries with pagination.
7. Add indexes to serve a measured access path; state which query they support.
8. Use transactions only for invariants contained within this PostgreSQL
   database. For SQL plus S3/Valkey effects, use retryable operations and
   explicit reconciliation/outbox behavior.
9. Load runtime credentials from `secret/<app>/postgres`; keep credentials and
   full connection strings out of source, images and logs.
10. Minimize personal/sensitive data. Define retention and deletion behavior,
   including dependent S3 objects and derived cache entries. Do not put secrets,
   authentication tokens or unnecessary sensitive values in logs or cacheable
   query results.
11. For every user-facing operation, test both allowed-owner and denied
    cross-user/cross-tenant cases. Include unauthenticated access, role
    boundaries, pagination limits and deleted/disabled account behavior.
12. Document the data owner, retention/deletion behavior and critical query
    latency in the app README.

## Reject or challenge

- A second database service without a demonstrated requirement.
- Large binary payloads stored as `bytea` by default.
- SQL assembled by concatenating request data.
- Unbounded result sets or indexes with no query justification.
- pgvector enabled only because it is available in the image.
- Returning vector matches before applying the user's tenant/document ACL in
  the database query; similarity is relevance, not permission.
- Returning a row solely because the client knows its identifier; every lookup
  must include the relevant authorization/tenant boundary.
- Treating hidden UI controls as access control or leaking whether another
  user's private record exists through error differences.

Explain the reason and the compute/operations avoided for each chosen pattern.
Configuration review cannot prove query plans, migration safety or data retention;
request evidence in tests or review. Before completion, walk through whose data
is read, changed and deleted, what happens on retry, how users recover from
errors, and what remains after account or record deletion.
