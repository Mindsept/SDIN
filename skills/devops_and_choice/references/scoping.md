# Ask the questions that change the service or operating decision

Start with the product and existing implementation. Reuse known answers and the architecture decision instead of asking the same questions again. Ask one to three questions at a time, in ordinary language. “No requirement” and “I do not know yet” are distinct valid answers.

## First decision round

| Topic | Ask when not already answered | Consequence |
|---|---|---|
| Outcome and ownership | What do users do, and which data must this application own rather than read from another system? | No service, authoritative PostgreSQL, integration adapter, or file storage |
| Durability and consistency | What must survive restart or host failure? What loss, duplication, staleness, or concurrent update is acceptable? | Source of truth, transactions, cache, idempotency, queue and restore design |
| Response and completion | Is there a response-time SLO or maximum wait for each important request? Must the complete result arrive then, or can a job finish later? | Sync path, cache/projection eligibility, worker, independent acceptance/completion targets |
| Access and sensitivity | Who may see, change, or delete each record/file? Are there tenants? May data leave the platform? | OIDC plus object authorization, private S3, tenant keys, LLM scope |
| Environment and policy | Workshop only or an operated service? Which existing architecture/team rules and decisions apply? | Applicable contract, migration, existing skill handoff, production gaps |
| Delivery and operator | Where will the application run? Which machine can reach the platform? Is GitHub Actions configured and who operates the target? | Hosted validation versus trusted platform-connected runner, credentials and release process |

Do not infer “internal” means nonsensitive, “cache” means disposable sessions, “AOF” means zero data loss, or “GitHub” means GHCR or a cloud deployment. Do not ask the user to choose Valkey or PostgreSQL before establishing data semantics.

## Conditional questions and explicit next decisions

| Trigger | Follow-up | Decision it changes |
|---|---|---|
| Proposed Valkey cache | Which query is expensive? Repeated under what load? Maximum stale age? Single or multiple API processes? What happens on miss, eviction, or outage? | Optimize SQL first; no cache / local bounded cache / shared Valkey. Reject cache if correctness depends on an unguaranteed TTL |
| Sessions/rate limits | Can sessions be invalidated by restart? Must logout/revocation be immediate? Is the limit approximate or security-critical? | Signed/stateless versus server sessions, durable session index, fail-closed/open policy, shared atomic counter |
| Async jobs | Can users accept `202`? Completion deadline, retry/loss tolerance, queue growth, cancel behavior, side effects? | Durable job/Stream pattern, worker capacity and idempotency; not Pub/Sub for recoverable work |
| Business workflow | Wait for humans/timers? Persist intermediate decisions? Multi-step retry or compensation? Workflow version changes while running? | Temporal under local policy; app task queues/namespaces and replay/versioning |
| Files | Size, type, private/public, upload frequency, versioning, retention and download consumers? | S3 versus small DB value versus rebuildable local temp file; authorization and orphan cleanup |
| Search | Exact filters/text search or semantic similarity? Corpus size, permissions, freshness, measured recall/latency? | Postgres indexes/full-text first; pgvector when semantics justify embeddings; extra engine only for a demonstrated gap |
| LLM | What capability requires a model? External data permission? Token/cost budget? Evaluation, output schema, provider failure? | APISIX routes and virtual key; possibly no LLM; RAG and worker not automatic |
| Identity/secrets | User login, workload identity, or admin provisioning? Which process needs which secret? Existing OIDC integration? | Casdoor versus OpenBao versus ordinary nonsecret config; no shared root token as runtime isolation |
| Analytics/logs | Product adoption question, latency incident, audit requirement, or business source of truth? Retention and sensitive fields? | Umami versus Dozzle/logs/metrics versus durable audit table; avoid recording everything everywhere |
| Images/releases | Local workshop registry only, or remotely reachable immutable releases? Existing image policy and rollback target? | Local registry versus explicitly configured GHCR/other registry; artifact identity and runner reachability |
| Deployment | Single host or independent environments? Allowed downtime? DB compatibility, data migration, rollback constraints? | Recreate versus staged rollout; deployment lock; migration ordering and restore plan |
| Reliability | RTO/RPO, restore destination, backup owner, storage/capacity limits, alert owner? | Actual recovery procedure; single development volume is insufficient for an asserted recovery guarantee |
| GitHub runner | Public/private repo, who can alter workflows, allowed runner groups/workflows, branch/environment protections? | Isolated untrusted validation and trusted operations; a YAML label alone does not enforce trust |

## SLO follow-up without jargon overload

If “maximum 200 ms” is ambiguous, ask whether every successful operation must finish by that deadline or whether a proportion such as 99% must finish within it. Record measurement start/end, route/journey, time window, traffic/concurrency, payload/data limits, cold conditions, and failure policy. Ask whether freshness or delayed completion can change; do not assume it can.

Examples of consequences to explain to the user:

- “If the database query is already within budget, adding Valkey is not justified. If repeated aggregation dominates and a 30-second-old result is acceptable, a scoped cache/projection becomes a candidate.”
- “If reports may arrive later, we can bound acknowledgment and completion separately. If the final report must be returned in 100 ms, a queue does not satisfy that requirement.”
- “If losing a session on cache restart is unacceptable, define a durable recovery/source-of-truth strategy before choosing the shared cache.”
- “If the workflow waits days for approval, the local Temporal rule applies; a continuously polling Stream consumer would add custom orchestration.”

No product SLO is a recorded fact, not permission to erase the workshop server p99 contract. Unknown load can be a dated assumption with a validation plan; unknown ownership, allowable data loss, or result semantics that changes correctness keeps that specific choice provisional.

## Scope and output

For a focused technology question, give the chosen branch, rejected branch, essential integration steps, evidence and revisit trigger. For a full service/delivery design, record the answers in the service plan and runbook. Reuse an existing plan rather than create duplicates.

A user request for analysis or a skill does not itself authorize running a platform start, provider call, release, restore, purge, or shared-resource migration. Do the authorized design and local reversible implementation first. Reuse any existing explicit execution authorization; do not invent an extra approval round for each harmless edit.
