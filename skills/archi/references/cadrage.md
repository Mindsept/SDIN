# Adaptive scoping and clarification

## Method

The skill must **discuss the need before settling on a solution** when requirements are insufficient. It must not turn every request into a full questionnaire. Record answers, sources, and uncertainties in the decision document, then ask only questions that could change a decision.

1. Read the brief, manifests, directory tree, and existing ADRs. A missing file does not prove that a business need is absent.
2. Restate the expected outcome and actors in one sentence. Identify a happy path and an important failure case.
3. Ask for one to three clarifications, explaining their impact. Prefer understandable options, with room for a free-form answer.
4. After the answer, explain what changes and continue. Do not repeat the whole list.
5. If information is still missing, record a dated and reversible assumption, an experiment to measure it, or a specific blocker. Do not treat silence as approval.

**CAD-001 — MUST:** every decisive choice rests on an answer, evidence, or a labeled assumption. Why: avoid a choice that cannot be defended. Compute: avoid building and operating the wrong components. Check: question/evidence/decision table and human review.

## First round: seven topics, not seven questions at once

| Topic | Useful wording | Decision affected | Is an unknown acceptable? |
|---|---|---|---|
| Product | "Who uses the application, and what are the three essential actions?" | Frontend only, CRUD, jobs, workflow; no framework choice before this | Not for a final decision |
| Policy | "Does the course require TS/Bun, or should we propose the best stack compatible with the platform?" | `strict-typescript` or `platform-compatible`; need for a waiver | Provisional strict profile, alternative in draft |
| Team / existing system | "Is this a new project or existing code? Which stacks can the team maintain?" | Reuse, language, migration, and learning cost | Assumption for exploration; confirm before a redesign |
| Data | "What data must be stored, who can see it, and for how long?" | SQL/S3, authorization, deletion, sessions, and identity | Unknown sensitivity or access scope blocks the affected data/security decision, not every independent stack recommendation |
| Deployment | "Is this a local demonstration, an internal tool, or an actually exposed service?" | Workshop/production configuration, availability, and secrets | Blocking for a production-readiness assessment |
| Constraints | "What is imposed: deadline, budget, library, language, network access, or hosting?" | Feasibility, tradeoffs, CI/SDK adaptation | Unknown deadline/load: assumptions possible; network prohibition: blocking for external AI |
| Response-time SLO | "Do you have a response-time SLO or a maximum acceptable request duration? For which operations, and must the complete result be returned within that time?" | Sync versus jobs/streaming, latency budget, cache/freshness, dependency feasibility, workload validation | An explicit lack of a product target is valid; preserve course targets. An unknown deadline/result requirement that changes feasibility blocks that choice |

Example of a useful opening message: "I understand this is a portal for submitting and viewing case files. Three points change the architecture: the course's strict profile or a free choice of compatible stack; whether human approval is required; and document access rights." Then ask the questions. Do not ask "Python or Java?" of a user who has not provided any use case.

The SLO topic is **always covered**, not reserved for a claim of high load. Obtain it from an explicit brief or ask in the first relevant rounds while keeping the one-to-three-question limit. Do not require the user to know SRE terminology: "When the user clicks Search, how long can they wait for usable results?" is a valid opening.

## Response-time clarification branch

**CAD-002 — MUST:** establish whether a response-time requirement exists and what counts as the result before recommending an execution strategy. Read [SLO-driven strategy](slo-strategy.md) and translate the answers into decisions, not just a list of requirements. Why: a fast acknowledgment can still fail the user's actual deadline. Compute: avoid queues, caches, or rewrites that do not solve the required latency.

Ask only the missing follow-ups that can change the choice, in small rounds:

1. **Target and operation:** "Which requests matter, and what time limit applies to each: search, save, upload, report, AI answer?" Do not apply one target to all operations without agreement.
2. **Meaning of maximum:** "Must every request finish before that deadline, or should a proportion, such as 99%, finish within it over a defined period? What should happen if the deadline is missed?" Record a hard deadline separately from a percentile target; a timeout does not guarantee a successful result.
3. **Result semantics:** "Must the full result be available in that time, or may the API acknowledge a job and return the result later? If later, by when? For streaming, when must the first useful output and the final output arrive?"
4. **Boundary and workload:** "Is the time measured in the browser or at the API? At what peak request rate/concurrency, payload size, and data volume? Should cold starts or cache misses be included?" Offer concrete examples if the user does not know RPS.
5. **Permitted tradeoffs:** "May results be slightly stale, precomputed, partial, or unavailable during dependency failures? Which operations require fresh authoritative data?" An accepted stale search result does not authorize a stale permission check or balance mutation.
6. **Evidence and authority:** "Is this a contractual/course requirement, a product goal, or a starting assumption? Are measurements available, and who can approve a changed target?"

If the answer is **no product SLO**, record that answer, explain the applicable workshop baseline, and propose a provisional per-operation target only if useful. Do not fabricate user agreement. If the answer is **unknown**, show what remains undecidable and explore alternatives; do not repeat a question already answered or force a user who asked for no questions to respond. A missing exact RPS estimate can be a reversible assumption; uncertainty between "full result in 100 ms" and "acknowledge in 100 ms, finish later" changes the architecture and remains blocking for that decision.

Example: "You require the complete search result in 100 ms at the API. I will first evaluate a bounded indexed query in the modular API. A background job would change that contract, and replacing Python with Go is not justified until measurements identify CPU/runtime overhead as the bottleneck."

## Conditional branches

| Trigger | Questions to ask | Consequence to examine |
|---|---|---|
| Public website / SEO | Editorial pages? Per-request personalization? Publishing frequency? Indexing required? | Default to SSG/build for stable content; SSR only if needed; SPA for an authenticated area |
| API / CRUD | Actors, authorization rules, volume, search, internal administration, imports? | Django/admin versus a dedicated API; monolith; ORM or SQL |
| Claimed high load | Observed or estimated RPS? Peak? Concurrency? Response size? p99 budget and available resources? | Representative benchmark; pools/backpressure; do not conclude from "a lot" |
| CPU computation | Which function dominates runtime? Existing CPU profile? Native library available? Batch or interactive? | Algorithm/vectorization before a new language; specialized worker only if useful |
| Scientific data / ML | Training or inference? Required libraries? GPU? Model sizes? Is external data processing allowed? | Scientific Python; separate worker if dependencies/resources differ; the platform does not provide GPUs |
| LLM / RAG | Source of truth? Retrieval needed, or just generation? Private documents? Error tolerance? Token budget and evaluation? | APISIX, pgvector if retrieval is justified, citation and access checks; no reflexive RAG |
| Asynchronous processing | Can the response be 202? Maximum delay? Cancellation? Recovery after a crash? Are duplicates tolerated? | Valkey Streams, job status, idempotency, bounded retries |
| Human approval | Waits of minutes or days? Reminders? Expiry? Compensation? Version changes while running? | Temporal and versioning policy; no permanent polling loop |
| Real-time behavior | One-way or bidirectional? Frequency? Acceptable latency? Reconnection? Ordering? | Infrequent polling, SSE, or WebSocket as needed; backpressure |
| Mobile / offline | Browser or native application? Local storage? Synchronization? Conflicts? Lost device? | Native client/PWA and API; no embedded platform secrets |
| Multi-tenancy | Isolation between organizations? Cross-tenant administrator? Export/deletion? Shared identities? | Object/tenant authorization, leakage tests, SQL schema; database per app ≠ database per tenant |
| Third-party integration | Pull/push? Limits, availability, usage rights? Idempotency key support? Offline mode? | Adapter/upstream, cache with provenance, fixtures, and failure strategy |
| Critical production service | Business impact of an outage? RTO/RPO? Maintenance window? Operational owner? | Backup/restore, redundancy to design beyond the workshop stack, deployment review |
| Existing application | What does not work? Evidence? Migration cost? Consumer compatibility? Rollback? | Targeted fix/strangler approach instead of a full rewrite |
| Required language | Educational choice, expertise, license, library, or preference? | Respect the choice; check feasibility and explain tradeoffs, without an unnecessary debate |

## Blocking questions and assumptions

Block only the **affected decision**, not the entire analysis. Examples:

- Confidential documents with unknown permission to send them to the LLM: do not declare the integration ready; examine uploads and the access model in parallel.
- Unconfirmed strict profile with a Python proposal: compare stacks, keep the final choice in draft, and do not fabricate a waiver.
- Unknown load for a small internal tool: propose a provisional capacity envelope, a test, and a review threshold; no anticipatory microservices.
- Unknown human approval delays: explain when a short transaction suffices and when Temporal becomes useful.
- A request to "not ask me questions": respect the instruction, provide visible assumptions and a provisional document; do not invent answers.

## Definition of "optimal"

Ask which objective dominates when objectives conflict: delivery time, maintainability, idle memory, computation time, throughput, latency, billed cost, portability, or team capability. Do not turn an arbitrary aggregate score into a scientific verdict.

For the two or three finalists, compare:

| Criterion | Expected evidence |
|---|---|
| Fit | Required capability and the library/framework providing it; distinguish built-in, extension, and custom implementation |
| Team | Declared expertise, team size, available support |
| Platform | Compatible SDK/runtime, OIDC/S3/Postgres/LLM/Temporal access as needed |
| Idle cost | Processes, memory, maintained connections, and storage, observed if tested |
| Cost under load | CPU/I/O/calls per user flow, test data, and concurrency |
| Deployment | Reproducible build, images, migrations, health checks, shutdown, and rollback |
| Reversibility | Boundary and cost of a change; avoid an abstraction that costs more than the risk |

A disqualifying criterion, such as an incompatible essential SDK, takes precedence over a preference. Missing measurements remain "to be measured," never zero. The best choice may be the language already maintained if another language's technical benefit is negligible.

## Completing scoping

Summarize the objective and exclusions, policy profile, possible decisions, open questions, assumptions, and next test or validation. Move to `ready` only when blocking unknowns are resolved and decisions are justified. `ready` means ready for review, not certified for production.
