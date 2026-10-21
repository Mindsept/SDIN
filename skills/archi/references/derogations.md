# Waivers: criteria, evidence, and expiry

A waiver is a deviation **from an applicable rule**, accepted by an authorized person, for a defined scope and duration. It is neither an allowed alternative nor an excuse after implementation.

## 1. Classify before requesting

| Situation | Treatment |
|---|---|
| Choice consistent with the profile and need | Reasoned decision, no waiver |
| Rule outside the scope, such as no database for a static site | `not applicable` + reason; no approval to request |
| SHOULD not followed for a good reason | Documented tradeoff; approval only if local policy requires it |
| Applicable policy MUST that needs to be set aside | Concrete waiver proposal, review, and approval from the designated authority |
| Impossible technical contract, such as frontend access to internal Postgres or occupied port 8200 | Correct the design; a document does not create a capability or free a port |
| Change to platform scope, such as another database, stronger isolation, or production infrastructure | Platform evolution decision; compatibility and provisioning must be designed; do not declare compliance with the v1 contract |
| Explicit authorization for the deviation already granted by the competent authority | Record it with provenance; do not ask a second time |
| Unknown authority | Prepare the proposal and ask who decides; do not sign on the instructor's behalf |

The user may choose a technology and change the proposed policy. This must not be disguised as institutional approval from the instructor. Respect the instruction while honestly describing its status against the course requirements.

## 2. Acceptable grounds and evidence

| Proposed deviation | Acceptable reason | Evidence / conditions | Reject or return to the standard if… |
|---|---|---|---|
| Python instead of TS under the strict profile | Essential scientific/ML library or significant existing system | Required dependency, alternative/interop comparison, runtime and CI cost, maintainer | Mere preference or no analysis of the need |
| Go/Rust for a hot spot | SLO or resources remain outside budget after reasonable optimizations | Representative profile, comparable benchmark, useful gain, limited boundary, rollback | "Faster" without measurements; database/network latency is the actual limit |
| Java/.NET | Existing systems, expertise, integration constraints, or domain justifying the stack | Existing code, migration time/cost, support, and resources | Adding a runtime to reproduce the same CRUD without a benefit |
| Temporal SDK in another runtime | Essential SDK compatibility not covered by the canonical runtime | Support documentation and integration test; targeted worker | Assumed Bun/SDK compatibility or an unnecessary rewrite of the entire application |
| Direct SQL instead of a recommended ORM | Complex query, bulk operation/report, query plan control | Parameterized SQL, result contract, single migration authority, EXPLAIN/test | Unsafe interpolation or unmanaged transactions |
| No ORM | Application without relational persistence, a few targeted SQL queries, or a deliberate SQL-first approach | Choice matrix and explicit migration/pool management | The team wants to avoid understanding transactions |
| Microservices | Demonstrated delivery/team/scaling autonomy or isolation | Ownership, data, contracts, operational capacity, cost | Splitting by table/layer or claiming "it scales better" |
| Specialized database/search engine | Need that Postgres/pgvector cannot meet within the measured envelope | Missing capability, measurement, operations, and platform integration plan | Simple RAG or search without evaluating Postgres |
| SSR / frontend backend | SEO, server personalization, or BFF requirement | Expected experience, cache, measurements, and deployment adaptation | All screens are static or private without an SSR requirement |
| Non-Alpine / multi-stage image | Native dependencies, glibc compatibility, compilation tooling | Reproducible build, minimal runtime contents, tests/signals | Habitual choice without checking runtime requirements |
| SLO >350 ms | Inherent limit, accepted experience, specific operation | Async comparison, end-to-end budget, measurement, dated decision | Hiding an N+1 query or bypassing measurements |
| Shutdown ≥10 seconds | Runtime/activity constraint that cannot be checkpointed in the short term | Drain/recovery mode, bounded delay, impact of forced termination, orchestrator change | Infinite waiting or unanalyzed data loss |
| Vulnerability without a fix | Essential dependency, assessed risk, compensating controls | Advisory/version, exposure, owner, dated remediation plan | Embedded secret, unassessed risk, or permanent exception |

**EXC-001 — MUST:** every waiver specifies the need, scope, rule, alternatives, evidence, accepted cost, owner, actual approval, expiry date, and exit plan. Why: keep the exception reviewable. Compute: avoid permanently multiplying stacks and services after the reason has disappeared.

**EXC-002 — MUST:** do not approve an exception yourself on behalf of a third party. A "recommended" note or a passing automated check is not approval. Why: preserve accountability. Compute: no direct benefit; traceability takes precedence.

**EXC-003 — MUST:** reassess at expiry or when the evidence is no longer valid, such as a new SLO, supported SDK, removed library, changed team, or fixed CVE. Why: an obsolete exception does not become the rule. Compute: remove overhead that is no longer useful.

## 3. Proportionate procedure

1. Identify the exact rule, its source, normative strength, and active profile. Check that it actually applies.
2. Prepare the concrete alternative: component, directory tree, resources, validation plan, cost, and rollback. Perform the analysis and already authorized reversible work before requesting approval.
3. Reuse existing evidence; otherwise run a spike or benchmark within an authorized scope. Do not deploy, delete data, or use a paid provider merely for the purpose of "measuring."
4. Compare at least the standard and the proposal; add a less invasive option if plausible.
5. If approval is required and absent, request it for the prepared proposal, naming the rule and authority. Continue independent work. Elapsed waiting time does not constitute approval.
6. Record approved/rejected/pending status, date, expiry, and owner. Implement only within the authorized scope. A language approval does not cover publishing or sharing data.

## 4. Machine checks and human review

JSON v1 is deliberately limited in scope. Do not invent IDs accepted by the script to fit every exception into it.

| ID | Meaning | JSON v1 waiver | Evidence that is not automated |
|---|---|---|---|
| `PLAT-001` | Public clients do not directly consume private services | No | Bundles and actual calls |
| `PLAT-002` | Valid canonical port block, excluding 8200 | No | Actual port availability on the machine |
| `DATA-001` | Vectors imply that Postgres is selected | No | Extension actually enabled and valid queries |
| `DATA-002` | ORM/query-builder/SQL access implies Postgres for the component | No | Correct choice and use of the tool and database |
| `READY-001` | Completeness and no blocking unknown in ready status | No | Honest answers and quality of justifications |
| `ARCH-001` | Applicable layers declared for an API | Yes, targeted component | Actual separation of responsibilities, imports, and SQL |
| `STACK-001` | Language consistent with the strict profile | Yes, targeted component | Expertise, CI adaptation, runtime/SDK, actual approval |
| `OPS-001` | Declared server health checks and bounded shutdown | Yes, targeted component or `*` | SIGTERM test, availability, and recovery |

Rules such as `PAT-*`, `ASY-*`, `SLO-*`, `PERF-*`, `SEC-*`, and those in the stack, structure, and data references are audited in the human-readable document. An exception to one of these rules is recorded in the ADR and review matrix, **outside the v1 `waivers` array**. Mention its status in the final report. Machine checks therefore cannot certify all applicable waivers. Changing a language profile does not change a response-time contract; record the affected operation, boundary, target, evidence, and actual authority for any approved SLO change.

In JSON, `approved_by` must identify an actual person or authority; `evidence` contains links or paths to the decision and its supporting evidence. The validator checks presence and dates, not identity or authenticity. An empty list means "no approved exception declared"; a pending exception belongs in the decision document and keeps the unknown blocking if the decision depends on it.

## 5. Example proposal without fabricated approval

"Extract image conversion from `worker` into a Rust worker. Measurements on the representative batch show that this CPU workload dominates elapsed time; reducing the format and resolution has already been considered. The API remains in the selected stack. Plan for an additional image and pipeline, the same job contract, and a configuration switch back to the original worker. Applicable rule: STACK-001 under the strict profile. Decision: pending approval from the course authority; expiry and signatory will be recorded only after approval."

This example contains no invented quantified gain. A Python requirement under `platform-compatible` is justified in the ADR; do not copy this waiver example to manufacture an exception.
