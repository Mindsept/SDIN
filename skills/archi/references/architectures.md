# Choosing an application architecture

Contents: decision procedure; styles; deployment and code boundaries; communication; synchronous/jobs/workflows; read models and caching; real-time/offline; AI; migration; worked decisions; review rules.

This guide is a **proposed policy**, tailored to the SDI foundation. It describes needs, not a universal ranking. Costs are categories to measure, not promised savings. Platform capabilities are detailed in [platform](plateforme.md).

## 1. Decide before drawing services

Read [SLO-driven strategy](slo-strategy.md) before recommending a request path. Ask whether a response-time SLO exists; identify its endpoint or user journey, percentile or hard deadline, measurement boundary, workload, and required outcome. An unknown target is an explicit unknown, not permission to claim that an architecture is fast enough.

Apply the questions in this order:

1. Can the result be computed at build time or in the browser? If so, avoid an always-running server.
2. Is a shared source of truth or access to secrets required? If so, an API/backend is necessary; do not move secrets into the client.
3. Does the business domain need several modules but a shared transaction and deployment? Prefer a modular monolith.
4. Is an operation slow, resource-intensive, or independent of the interactive response? Consider an asynchronous job.
5. Must progress be preserved across several steps, restarts, or a wait for human input? Consider Temporal.
6. Does a boundary genuinely need independent deployment, scaling, or ownership? Only then consider a standalone service.

For each answer, apply the competing-choice rules below. Do not stop at naming an architecture or listing its generic advantages.

**PAT-004 — MUST:** write each consequential selection as: **requirement → selected pattern → rejected alternative and reason → evidence or validation plan → condition for reconsideration**. State what would make the alternative preferable. If a blocking fact is missing, ask for it or provide a conditional decision; do not silently replace it with an assumption. Compute: compare total deployed cost, including idle processes, reads, retries, synchronization, and operator effort.

Make four separate decisions; they are not competing answers to one question:

| Decision axis | Alternatives to decide between | Valid combined example |
|---|---|---|
| Deployment topology | Static-only, one backend, backend + worker, several independently deployed services | One modular backend plus one document worker |
| Code organization | Feature-first or responsibility-first; simple layers; selective ports/adapters | Feature-first modules, layered responsibilities inside each module, ports around external providers |
| Execution contract | Complete synchronously, accept a job, coordinate a durable workflow | Synchronous reads, queued exports, Temporal for approvals |
| Read/write model | Direct authoritative queries, cached results, projections, separate command/query models | Transactional writes and a read-only dashboard projection |

For example, **a modular monolith can use vertical slices and hexagonal boundaries at the same time**. A queue does not require microservices. CQRS does not require event sourcing, separate processes, or a second database. An API and its worker can be two deployments of the same application codebase. Name the axis whenever comparing alternatives.

**PAT-001 — SHOULD:** start with the minimum number of processes that meets the constraints, then justify each additional always-running process. Why: fewer network contracts and combined failures. Compute: avoid unnecessary idle memory, pools, serialization, and deployments. Evidence: component → need → cost inventory.

## 2. Architecture style matrix

| Style | Suitable cases | Signs it is unsuitable | Structure and SDI services | Cost avoided / cost accepted |
|---|---|---|---|---|
| Static site / SSG | Documentation, showcase site, infrequently changing catalog, single-player game, local computation | Secrets, shared private data, essential server-side personalization | Frontend served by nginx; no DB/API by default; S3 assets only if useful | Avoids server rendering per visit; measure the build required for each publication |
| SPA + API | Interactive authenticated area, dashboard, business tools | A few stable public pages | Frontend, modular API, Postgres for durable state, Casdoor for login | Separates asset caching and business logic; monitor JS/client cost |
| Server rendering / SSR | Personalized initial HTML, justified dynamic SEO, need for a BFF | Using SSR only because the framework supports it | Declare and operate the rendering backend; adapt the nginx template, health checks, and ports | Server cost per request and fragmented caching; demonstrate UX/SEO benefit |
| Modular monolith | Small/medium team, related domain, strong transactions, shared delivery | Demonstrated need for independent deployments by several teams | Business modules, controllers/services/adapters; shared Postgres for the app | Avoids interservice networking and distributed coordination; requires tested internal boundaries |
| Layered architecture | CRUD/API with stable responsibilities | Classes and conversions with no benefit | Transport → application; domain; infrastructure. Refer to framework mappings | Reduces coupling; a few in-memory calls, not a network service per layer |
| Ports and adapters / hexagonal | Complex domain, multiple integrations, core to test in isolation | Trivial CRUD where ports/interfaces add nothing | Ports around volatile dependencies; S3/LLM/DB adapters | Facilitates changes and tests; accepts code cost without automatic runtime benefit |
| Vertical slices | Autonomous modules within an app, changes concentrated by capability | Copying auth/logging/DB everywhere | Feature-first, with responsibilities separated internally | Limits cross-cutting changes; reuse mechanisms without sharing everything |
| API + job workers | Imports, exports, PDFs, OCR, conversions, document ingestion | A simple operation fits within the interactive budget | Valkey Streams + Postgres status if durable, S3 for files, tracking API | Smooths peaks and releases connections; adds worker, queue, and duplicate handling |
| Durable workflows | Human approval, long waits, compensatable steps, recovery; even one task when durable execution/tooling is justified | Simple task already adequately served by an existing durable job mechanism, or a noncritical local timer | Temporal, namespace per app, compatible worker; operator UI | Avoids polling/persistent loops and custom recovery; size history/workers appropriately |
| Microservices | Autonomous teams, distinct delivery cadence, demonstrated isolation or asymmetric scaling | Single team, services organized by table/layer, constantly distributed transactions | Several deployable units, explicit ownership, versioned contracts | Network, observability, CI, memory, and consistency cost; prove isolation/autonomy benefits |
| Events | Several independent consumers of a business fact, need to reduce temporal coupling | RPC chain disguised as events with an immediate response required | Versioned events; Valkey if suitable; outbox if atomicity is required | Reduces synchronous waiting; manage duplication, ordering, retention, and replay |
| CQRS | Reads differ substantially from writes, expensive projections whose cost can be amortized | Simple CRUD, “modern architecture” as the only reason | Start with two paths in the same app/DB; external projection only if necessary | Tailored read queries; projections and possible lag add cost |
| Event sourcing | Essential replayable business history, well-defined temporal semantics | Basic audit, reference history, or lack of understanding of event migrations | Explicitly designed business-fact log, versions, projections, and snapshots | Replay and storage cost resources; do not confuse it with Dozzle logs or Temporal history |
| CLI / one-off batch | Administrative export, local transformation, developer tool | Ongoing interactive multi-user usage | Command entry point → service → adapters; no /health server for a terminating CLI | Avoids a resident container; plan recovery, exit codes, files, and memory limits |
| Native client / offline PWA | Sensors, OS integration, operation without connectivity, mobile app | Simple web viewing with no native requirement | Client + API; local cache and sync protocol; never embed platform credentials | Accepts the cost of two environments and sync for hardware/offline needs |
| Serverless / functions | Rare events, deployment environment that genuinely supports them | Introducing a new control plane into the workshop for a demo | Treat architecture outside the foundation separately; `gitlab-ci-local` is not a FaaS runtime | Potential to stop while idle, but measure cold starts, duration, unit cost, and limits |

### Rendering: choose per route, not by framework branding

| Conditions | Select | Alternative rejected | Evidence / reconsideration trigger |
|---|---|---|---|
| Public content can be generated before the visit and refreshed through publication/build | Static/SSG | Per-request SSR for identical content | Publication freshness, build duration and browser performance meet the need; switch only when required content cannot be generated ahead of time |
| Authenticated interactive workspace; an initial client shell is acceptable; API handles secrets/private data | SPA + API | SSR solely because “professional apps use SSR” | Measure initial load and interaction on the target device/network; reconsider if initial useful content or required public indexing cannot meet the objective |
| Initial HTML must contain current request-specific content, and a client render or prebuilt page cannot satisfy the stated requirement | SSR with a declared server component and bounded data fetching | Static pages that violate personalization/freshness, or an SPA that demonstrably misses the initial-content need | End-to-end initial-content budget includes rendering and upstream calls, plus cold/warm behavior; reconsider if client/static rendering now meets the same requirement at lower cost |
| Public pages suit pre-rendering while the private workspace needs interactive client behavior | Hybrid by route with an explicit boundary | Applying the most expensive rendering mode to every page | Route inventory states render mode, private-data/cache rules, and deployment needs; simplify if maintaining both modes exceeds the measured benefit |

A BFF is a client-specific server boundary for aggregation/session or adaptation needs; it is not by itself a reason to server-render HTML. Keep it within the existing backend when that meets the requirement. Add a separate BFF deployment only for an identified independent client contract, lifecycle, or isolation need, with its extra hop included in the SLO budget.

## 3. Monolith, modules, and deployment units

### 3.1 Choose a modular monolith or a separately deployed service

Use this table for each proposed capability boundary. A high request count alone does not select microservices; check the bottleneck, scaling unit, and actual capacity.

| Observed conditions | Select this | Reject / defer this | Required evidence | Reconsider when |
|---|---|---|---|---|
| Related capabilities, one release owner, frequent cross-capability transactions, no demonstrated independent scaling need | Modular monolith with explicit business modules | Service per table, per endpoint, or per technical layer | Module ownership and one representative transaction path | A stable capability needs independent releases, isolation, or scaling that the current deployment cannot satisfy |
| One expensive task slows interactive traffic, but both use the same business model and release cadence | Same app with a bounded worker/process for that task | Splitting every module into a microservice | Profile shows contention; separate worker capacity and queue/completion budget are feasible | This worker becomes an independently owned capability with a stable contract and separate lifecycle |
| A stable capability has a real independent owner/release cadence or measured isolation/scaling requirement, and can own its data/contract | Separate service for that capability; keep other capabilities together | Whole-system decomposition for symmetry | Boundary, owner, contracts, data ownership, operational capacity, and before/after latency/cost estimate | Benefit disappears, coordinated releases become routine, or cross-service calls dominate the response budget |
| A proposed split requires several synchronous calls or a cross-service transaction for almost every operation | Keep those capabilities together, or redraw the business boundary | A distributed monolith joined by chatty RPC or shared writable tables | Trace/use-case map and transaction invariants | A product change creates a genuinely independent boundary or permits explicit eventual consistency |
| The request SLO is missed by slow SQL, remote-provider latency, or an inefficient algorithm | Optimize or redesign that dependency/path first | Microservices as an automatic latency fix | Critical-path profile under the agreed load | A measured resource or failure boundary remains after local fixes |

Fault isolation requires a corresponding dependency and failure design. A service that must synchronously wait for another unavailable service cannot promise an independent successful response merely because it runs in another container.

### 3.2 Choose layers, ports/adapters, and vertical slices deliberately

These choices concern **source boundaries**. They do not add network hops by themselves. Keep mandatory responsibilities separated wherever they exist; vary the amount of abstraction with actual complexity. See [concrete structures](structures-code.md).

| Condition | Explicit choice | Why the competing choice is weaker here | Evidence / exit trigger |
|---|---|---|---|
| Small CRUD application, few use cases, one transport, one DB, little domain behavior | Simple transport → application → persistence responsibilities; pure domain functions only where rules exist | An interface, generic repository, factory, and mapping layer around every trivial call add maintenance without isolating a real variation | Trace one change end-to-end; add a port when a volatile dependency or independent domain test requires it |
| Several business capabilities evolve separately within the same deployment | Feature-first modules / vertical slices, preserving responsibilities within each slice | Global `controllers/`, `services/`, `repositories/` folders scatter each business change and can conceal cross-module coupling | Map imports and changed files per feature; split shared mechanisms from shared business ownership |
| Complex invariants must be tested without HTTP/DB, or several transports/integrations use the same use case | Application/domain core with ports and external adapters, usually inside feature modules | Framework objects and provider SDK types flowing through the core tie business rules to infrastructure and slow focused tests | Demonstrate a core use-case test without external infrastructure and an adapter contract test; remove unused speculative ports |
| One unstable external provider sits inside an otherwise simple CRUD application | Add a narrow port/adapter for that provider only | Rebuilding the entire app as a generic hexagonal framework exceeds the actual variation | Provider substitution/error handling is isolated; broaden only when another dependency has the same concrete need |
| High-throughput endpoint has measured mapping/allocation overhead | Preserve logical boundaries but simplify the measured hot path, data projection, or unnecessary copies | Removing authorization/domain boundaries or deploying layers separately does not follow from allocation measurements | Profile and behavior tests show the same semantics; revisit only if the material overhead remains |

**Do not choose hexagonal architecture because the SLO is tight.** Choose it for dependency direction and change/test isolation. **Do not reject it as inherently slow:** measure the concrete allocations and calls. Likewise, vertical slices describe change locality; they do not waive application authorization, persistence boundaries, or domain invariants.

An `api` component can contain several domains: cases, business permissions, search, publications. A `worker` can reuse the same application services through another entry point. Sharing code does not mean sharing a transaction across processes.

**PAT-002 — MUST:** do not split into `controller-service`, `business-service`, and `repository-service` processes. These are code responsibilities. Why: preserve a coherent unit. Compute: eliminate unnecessary network round trips and conversions. A waiver is possible only when a real deployment boundary is established, not to follow a layered diagram.

**PAT-003 — MUST for microservices:** justify each boundary with an owner, API/events, owned data, autonomy requirement, isolatable failure, budget, and compatibility strategy. Why: avoid a distributed monolith. Compute: no additional instance or pipeline without measurable benefit. Human review + contract tests.

The SDI convention provides **one DB/user per app**, not automatic database provisioning per microservice. For several services within an app, declare the owner of each table and of migrations; do not allow several services to modify the same schema freely. If independence requires several DBs/buckets, document changes to bootstrap, secrets, and contracts. The v1 validator does not model this detailed topology.

## 4. Communication: choose according to need

| Mechanism | Choose when | Plan for | Avoid |
|---|---|---|---|
| Function call | Same process, immediate consistency required | Typed errors and module boundary | Networking to enforce layers artificially |
| REST/JSON | Business API, browser/mobile interoperability, and simplicity | OpenAPI, stable errors, pagination, versioning, and timeouts | Exposing ORM entities directly |
| GraphQL | Several clients with varying read needs, justified aggregation | Field/object authorization, depth/cost, batching, caching | Simple CRUD with hidden N+1 and unbounded queries |
| gRPC | Typed internal contracts, streaming, and demonstrated operational need | Protobuf/versioning, suitable browser client, tooling | Imposing gRPC on the browser or choosing it because Temporal uses it |
| Polling | Infrequent progress updates, simple deployment | Backoff, stop at terminal state, deadline, and capacity | Very frequent or infinite loops |
| SSE | Server → browser notifications, job progress, tokens | Reconnection, heartbeat, connection limit, streaming proxy | Using WebSocket when no continuous client messages are required |
| WebSocket | Bidirectional collaboration, multiplayer games, frequent interactions | Reconnection, maximum throughput, ordering, authentication, and bounded buffers | Promising message durability without a log/recovery mechanism |

Endpoints and budgets are determined by load, not a “REST is slow / gRPC is fast” rule. For a single-player game, the loop stays in the browser; a multiplayer gaming platform is a different requirement.

Make the client interaction explicit:

- Choose REST for ordinary browser/mobile business operations unless a concrete client need justifies another protocol. Choose GraphQL when clients genuinely need differing compositions and the team can bound and authorize that query surface; do not choose it solely to hide slow backend joins.
- Choose polling when updates can be infrequent enough to meet the product's freshness requirement at acceptable request volume. Switch to SSE if one-way events must reach many connected clients more promptly and connection capacity/reconnection behavior have been validated. Choose WebSocket only when sustained bidirectional messages justify its lifecycle and backpressure work.
- Choose gRPC for an internal typed/streaming contract when its integration and measured payload/throughput benefit justify the extra tooling. If the SLO miss comes from the database or provider, changing HTTP serialization alone is not the selection argument.
- Stream a response when incremental output is useful to the user. Record time to first useful output **and** time to complete output. Receiving a first token, heartbeat, or empty chunk does not satisfy a full-answer SLO.

## 5. Asynchronous and durable processing

### Select synchronous completion, a queue, or Temporal

Resolve **what the caller must receive before the deadline** before moving work out of the request. Use the [SLO contract and critical-path budget](slo-strategy.md); the rows below are decisions, not universal duration thresholds.

| Conditions that must be established | Choose | Do not substitute | Evidence and condition for switching |
|---|---|---|---|
| The caller needs the completed result immediately, and the complete authorized path fits the request SLO under representative load | Synchronous use case in the API | A queue just because the operation writes data or invokes a service | Load test includes dependency/pool wait and response serialization; revisit if the complete path loses its required margin |
| Completion is necessary immediately, but the measured critical path exceeds the response budget | First reduce required work, optimize the bottleneck, precompute where semantics allow, or negotiate a different requirement | A fast `202`, first token, or runtime rewrite presented as meeting the original completion SLO | Demonstrate a feasible revised critical path; if a required uncached dependency alone exceeds the budget, explicitly state infeasibility until the dependency or requirement changes |
| The caller accepts later completion, and the work is an independent recoverable unit such as an export or conversion | API + bounded job worker and explicit status/result contract | Temporal solely because a single job takes a long time | Durable acceptance, idempotent effects, queue-age + processing-time + retry budget fit the separate completion SLO; switch if the process gains durable coordination requirements |
| Several steps must retain business progress across crashes, wait for external/human input, or coordinate timeouts/compensation | Temporal workflow + activity worker, with state/status visible to the caller | An ad hoc chain of timers/status columns/retry scripts whose recovery semantics are not designed | State-transition and failure map, SDK/runtime compatibility, replay and retry tests; simplify if an existing durable job mechanism meets the same needs at lower total cost |
| A noncritical best-effort effect may be dropped on process exit and has no durable delivery requirement | In-process task may be sufficient if bounded and documented | In-process work presented as durable completion or retryable acceptance | Explicit loss tolerance and shutdown behavior; switch to durable jobs when loss would violate a product requirement |
| One business fact has several independent consumers that may finish later | Publish an event with consumer-specific delivery/recovery contracts | A request/reply chain disguised as events while the caller waits for every consumer | Fact ownership, consumer lag/freshness budgets, versioning and replay needs; use a direct call when only one immediate consumer/result is required |

**ASY-006 — MUST:** justify asynchronous architecture with both an allowed asynchronous user contract and a feasible completion budget. A queue absorbs a temporary burst; it does not create processing capacity. Check arrival rate, sustainable service rate, oldest-job age, concurrency/resource limits, and permitted delay. Under sustained excess demand, choose admission control, reduced work, additional proven capacity, or a changed requirement; do not promise that unbounded buffering meets an SLO.

**ASY-007 — MUST:** if the process includes human waiting, define separately the technical response/step SLO, the business completion target, and escalation/expiry behavior. Temporal can preserve progress and timers; it cannot guarantee when a person responds or when an unavailable external provider recovers.

A single independent task does not categorically exclude Temporal: compare it with the existing durable job mechanism if its recovery, retries, or operational tooling reduce the code the team must maintain. Select the simplest mechanism that actually meets the durability contract; task count and duration alone do not decide. The examples below reject unjustified orchestration, not durable execution that solves a demonstrated need.

### Independent jobs: Valkey Streams

Proposed flow: `POST /jobs` validates and authorizes → durably records/enqueues according to the contract → returns `202` and an identifier → worker retrieves and processes → terminal status can be queried. `202` does not mean the operation has completed. Large content belongs in S3; the message references the object and a version/checksum.

**ASY-001 — MUST:** define idempotency, acknowledgment, recovery of abandoned jobs, attempt count, backoff, timeout, dead-letter queue, and shutdown. Why: a crash can cause reprocessing. Compute: avoid duplicate processing and unbounded retries. Do not promise exactly-once execution; make business effects idempotent.

**ASY-002 — MUST if a SQL write + event must be atomic:** specify a consistency mechanism (e.g. an outbox in the SQL transaction, followed by a publisher). Why: writing and sending involve two separate systems. Compute: accept additional reads/publisher to avoid lost events and manual repair. If atomicity is unnecessary, explain why before adding an outbox.

**ASY-003 — SHOULD:** limit concurrency and batch size to Postgres, provider, and memory capacity. Why: increasing worker count can saturate the shared dependency. Compute: avoid congestion, errors, and repeated computations. Checks: saturation, queue depth/age, and processing duration.

### Durable processes: Temporal

The workflow coordinates; activities perform I/O and business effects. Specific APIs depend on the selected SDK. Plan namespaces, task queues, stable identifiers, deadlines, retries, signals/updates, cancellation, compensation, history limits, and versioning policy. The worker is part of the app: the Temporal server does not execute business logic on its own.

**ASY-004 — MUST:** keep workflow code deterministic and place LLM/HTTP/DB calls and other effects in activities; design those effects for retries. Why: replay compatibility. Compute: replaying a historical decision must not repeat a billable call. Sources: [Workflow definition](https://docs.temporal.io/workflow-definition) and [Activity definition](https://docs.temporal.io/activity-definition), accessed October 14, 2026; verify the details of the chosen SDK.

**ASY-005 — MUST:** document deployment with workflows in progress, relevant replay tests, migration/versioning, and the outcome of compensation. Why: a new worker must not invalidate history. Compute: avoids full restarts and duplicate processing. Temporal does not automatically make a distributed transaction atomic.

Do not systematically duplicate Valkey and Temporal for the same process. They can coexist for two explicitly different needs. Do not present namespaces as a strong security boundary in this stack without auth/mTLS.

## 6. Direct queries, caching, projections, CQRS, and event sourcing

Choose the least complex read strategy that satisfies **both latency and correctness/freshness**. A cache hit target without miss/rebuild behavior is incomplete. Decide whether the same actor must immediately read their own write before choosing eventual consistency.

| Observed requirement or bottleneck | Explicit choice | Exclude / defer | Evidence and switching trigger |
|---|---|---|---|
| Ordinary CRUD; optimized authoritative queries fit the read SLO; fresh values are required | Direct queries against the app's Postgres through the persistence boundary | Cache, separate read store, event sourcing | Query plans, realistic cardinality, indexes, pool wait, transaction behavior; reconsider only when a measured read/load issue remains |
| Public or safely scoped results are repeatedly requested; recomputation is material; a defined stale interval is acceptable | Bounded cache of selected results; use Valkey only when shared caching is needed | Blanket caching of every response or authorization decisions | Hit/miss behavior, invalidation/TTL, tenant/user scope, cold-cache load and failure policy; remove if the hit rate or cost benefit does not justify it |
| The requirement allows build/publication-time freshness, and there is no per-request private computation | Pre-render or generate static content | An always-running SSR backend or DB-backed cache for identical public output | Build/publication delay, invalidation/publication semantics, client result; switch to dynamic rendering only when required personalization/freshness cannot be represented safely |
| An expensive join/aggregation is repeatedly served and an explicit projection lag is allowed | Precomputed read projection/materialized view, initially in the same app/DB | Separate deployment/store just to name the design CQRS | Rebuild/refresh cost, maximum lag, version/backfill plan, source-to-projection reconciliation; separate storage only if measured needs justify it |
| Read shapes and write invariants differ substantially; independent command/query models reduce real complexity or capacity contention | CQRS, starting with separate code paths/models in the same app/DB | Event sourcing or separate infrastructure as an automatic prerequisite | A read and a write use case showing the benefit, freshness/read-your-writes policy, operational cost; retreat to ordinary CRUD if model duplication dominates |
| The authoritative business model requires replay of immutable business events and reconstruction of state at meaningful points in time | Event sourcing only with explicit event evolution, projection, replay, and operational design | Event sourcing for ordinary audit logs, “undo” alone, or because Temporal retains workflow history | Domain/event model and versioned replay/restore tests; if the need is only traceability, select an audit trail instead |

**PAT-005 — MUST before caching or projecting:** document cache/projection key scope, invalidation or refresh rule, acceptable staleness, miss/rebuild behavior, permissions, and source of truth. For private data, avoid serving a formerly permitted result after permissions are revoked unless a specifically accepted policy covers that delay. Never drop required authorization checks to hit a latency target.

**PAT-006 — MUST:** compare cached and uncached paths under the declared traffic distribution. If misses violate the SLO, show that their frequency and behavior remain compatible with the actual objective, or redesign the miss path/admission/freshness contract. A high average hit rate does not by itself prove a tail-latency or hard-deadline guarantee. A cache can reduce repeated work; a new cache dependency can also introduce its own failure/latency costs.

CQRS separates responsibilities; event sourcing changes the authoritative storage model. They can be combined, but select each independently. These properties are supported by the official [CQRS](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs) and [cache-aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside) documentation (accessed October 14, 2026). The detailed selection gates here are this skill's policy.

## 7. Offline clients and collaboration

Decide which data is authoritative, what is local, permissions while disconnected, local retention periods, and the conflict-resolution algorithm. Define incremental synchronization, deletion tombstones, cursor/version, repeated sends, conflict detection, and logout/revocation. A CRDT is relevant only with well-defined concurrent operations; it does not remove business authorization requirements.

**CLI-001 — MUST for public clients:** never embed an OpenBao key, LLM provider key, OIDC client secret, or SQL/S3 administration account. Why: the client is controlled by its user. Compute: cost is not the driver; confidentiality and control over calls are required. Mediate through the API; verify the exact OIDC/public-client mechanisms at implementation time.

## 8. AI and RAG without unnecessary components

Choose separately: simple generation; structured extraction; text search; vector search; RAG pipeline; AI-assisted actions. Summarizing a document may require neither a vector database nor durable orchestration. Keyword search can remain SQL/full-text.

For RAG: original document in S3 → extraction → versioned chunking → embeddings through APISIX → metadata/vectors in Postgres → permission filtering before returning results → passages used for the answer. Plan chunk and vector updates/deletions when the document changes. Store the model version and chunking parameters; do not regenerate vectors on every read.

**IA-001 — MUST:** enforce permissions and tenant boundaries during BOTH ingestion and search; high similarity grants no read permission. Why: avoid exposing private sources. Compute: accept additional filtering, reducing the corpus/search scope when possible.

**IA-002 — MUST:** set token budgets, context length, retries, timeouts, concurrency, and evaluation sets. Why: cost and behavior vary. Compute: avoid unnecessary calls, context, and loops. The APISIX technical budget does not replace a business limit per session or cost tracking.

**IA-003 — MUST for generation from external content or RAG:** treat retrieved documents and any instructions they contain as untrusted data, never as authorizations or system rules. Plan for prompt injections, unsupported answers, missing citations, and out-of-scope requests, even if the app only displays an answer. Why: preserve boundaries and useful answer quality. Compute: accept validation and evaluation costs; limit retries that do not address missing evidence.

**IA-004 — MUST if external actions are performed:** model output is neither trusted code nor authorization. Validate the schema, allowed capabilities, and requester permissions before the effect; retain any required human approval. Why: prevent generation from triggering an out-of-scope action. Compute: accept validation cost; bound tool loops, retries, and billable calls.

## 9. Migration and evolution

Do not change languages based on a performance hunch. Profile first; fix N+1, indexes, algorithms, payloads, caching, and concurrency. If one part remains over budget, isolate that function or worker; compare a native library or specialized process with a complete rewrite.

For a migration: map consumers and data; define interface compatibility; expand/contract schema migration; limited coexistence; reversible switchover; stop criteria; actual removal of the old path after verification. Measure the temporary overhead of running both paths.

## 10. Worked decisions: apply the rules, not a pattern checklist

These are conditional design examples, not measurements of this repository or exemptions from its performance contract. Fill in actual load, SLO values, and measurements with [SLO-driven strategy](slo-strategy.md).

| Brief and evidence to establish | Concrete recommendation | Alternative rejected and why | What would change the recommendation |
|---|---|---|---|
| One-person offline-capable browser game, no accounts or shared scores, no server-held secret | Static frontend; game loop and local state in the browser; measure frame/input performance on target devices | API, worker, DB, or WebSocket: none serves a stated requirement; HTTP server p99 does not measure the game loop | Shared authoritative multiplayer state requires an authenticated server and a tick/message budget; optional score sharing adds only the needed API |
| Internal case-management tool with forms, permissions, and linked transactional updates; one team; optimized request path meets its SLO | Modular monolith, feature modules with simple layers, direct authoritative SQL via the selected persistence adapter | Microservices and event-sourced aggregates: they add distributed consistency or event evolution without a stated need | A proven independently owned capability or replay-as-business-model requirement appears; a dashboard read bottleneck alone first changes that read path |
| Private dashboard repeats expensive aggregate reads; users explicitly accept a bounded data delay; measured queries miss the response SLO | Precompute the aggregate, expose freshness, check actor/tenant access, keep ordinary transactional writes | General-purpose microservices or changing language first: the repeated DB aggregation is the measured bottleneck | Freshness becomes immediate, projection cost exceeds benefit, or the read workload needs independently proven capacity |
| A document export exceeds the interactive completion budget, and the user accepts later download | Authorize/accept durably, return job ID, queue a bounded export worker, store output in S3, expose status; separate acceptance and result SLOs | Claiming compliance from a fast `202`; choosing Temporal without showing that its recovery/tooling improves on the simpler adequate durable job mechanism | Exports gain resumable business stages, human approval, compensation, durable timers, or a demonstrated benefit from Temporal's recovery/tooling |
| Document approval waits for reviewers and then calls several systems with compensatable effects | Temporal workflow; effects in activities; explicit approval state, deadlines and compensation; prompt status responses | A synchronous request held open until approval, or a chain of unowned background timers | The business process becomes one short atomic operation; unrelated independent conversions can remain ordinary jobs |
| A required fresh provider/LLM result alone exceeds the full-response deadline | State that the current synchronous requirement is infeasible; examine precomputation, an allowed stale answer, a faster suitable provider, or a revised product contract | Rewriting the API in Go/Rust or streaming one token as proof that the full-answer target is met | A measured dependency path fits the budget or the user explicitly accepts a different outcome/deadline |
| A single CPU-heavy transform saturates the API and causes unrelated requests to miss their SLO | First optimize the algorithm/native library; then isolate and bound that transform in a worker if later completion is allowed, or in a capacity-isolated synchronous process if the full budget remains feasible | Whole-app language migration or unbounded parallel tasks: neither follows from a single isolated hotspot | Representative profiling proves the remaining runtime cost dominates and a narrowly scoped specialization meets the same behavior and budget |
| Independent teams need independent releases of stable capabilities with distinct data ownership; measured boundaries fit request and failure budgets | Extract only those capabilities as services; use direct or asynchronous contracts according to result and consistency requirements | A single release unit if it blocks the demonstrated autonomy; also reject service-per-layer/table | Operations cannot support the added complexity, coordinated release/transaction requirements return, or critical-path network overhead erases the benefit |

For an unresolved brief, the output remains conditional: “Choose direct authoritative reads if fresh results fit the budget; choose a projection if lag is acceptable and repeated aggregation is the measured bottleneck.” Ask the missing freshness/SLO question before turning that into an unconditional recommendation.

## 11. Mandatory review questions when applicable

- Can a component be removed without losing a requirement? If so, why does it exist?
- Does the critical path contain a network service for each technical layer?
- Does a failure or timeout leave the user with an explainable status and a recovery path?
- Are data, deployment, and team boundaries consistent?
- Which costs are actually measured, and when should the choice be revisited?
- Do advanced patterns (CQRS, event sourcing, microservices, CRDT) have an explicit need and test strategy?
- For each chosen pattern, is the rejected alternative named, and is there a concrete condition that would make it preferable?
- Does the SLO measure acceptance, first useful output, or completed outcome; does the selected execution contract actually meet that definition?
- Have timeout, dependency failure, cold cache, backlog, and data freshness been considered rather than only the happy-path average?

Additional external sources: [microservices and their tradeoffs](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices), [CQRS and when not to use it](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs), accessed October 14, 2026. These sources support the properties and tradeoffs; the `PAT-*`, `ASY-*`, `CLI-*`, and `IA-*` rules are this skill's proposed policy, not vendor rules.
