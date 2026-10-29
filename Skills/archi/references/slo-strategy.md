# Turning response-time SLOs into architecture decisions

Read this reference before deciding how critical requests execute. Its decision rules are this harness's proposed engineering policy. They do not promise a latency for a language or framework. Use [language/framework comparisons](langages-frameworks.md) and [pattern selection](architectures.md) to apply the resulting constraints.

## 1. Establish the contract before optimizing

**SLO-001 — MUST:** ask whether a response-time SLO or maximum acceptable duration exists, unless the brief already supplies the answer. Record one contract per critical operation or coherent operation class; do not replace the user's requirement with the easiest metric to satisfy. Why: an architecture must deliver the required result, not merely respond quickly. Compute: avoid optimizing the wrong path.

An SLI is the observed indicator; an SLO is its target. A latency percentile describes a distribution, not a guaranteed maximum. A timeout/deadline limits waiting or triggers cancellation/error handling; it does not guarantee a successful result. The maximum observed during a test is not a bound on every future request. Sources: [Google SRE, objectives](https://sre.google/sre-book/service-level-objectives/) and [gRPC, deadlines](https://grpc.io/docs/guides/deadlines/).

Complete this worksheet at the level needed for the decision. Ask missing questions in small rounds using [the questionnaire](cadrage.md).

| Field | What must be explicit |
|---|---|
| Operation | Route template or user journey; distinguish search, save, upload, export, and AI generation |
| Required outcome | Complete usable result, durable acceptance of a job, first useful streamed output, or finished job |
| Measurement boundary | Start and end events: browser click to rendered result, API ingress to final response byte, job acceptance to result availability, etc. |
| Target and statistic | Threshold and units, percentile or required proportion of good events; clarify an ambiguous “maximum” |
| Time window | Rolling/calendar observation window, or explicitly a workshop test acceptance window; do not present a short test as a production guarantee |
| Workload envelope | Arrival rate/bursts, concurrent users, payload/result limits, data volume, network/location, CPU/memory limits |
| Success and failures | Eligible requests; correctness, errors, timeouts, rejections, canceled requests, and degraded outcomes; define exclusions instead of hiding failures |
| Freshness and consistency | Permitted data age, stale/partial output, authoritative checks, and whether a delayed result is acceptable |
| Cold behavior | Whether startup, cache misses, connection setup, and model warmup are in scope; separate targets only when explicitly justified |
| Deadline behavior | What the client sees on expiry; cancellation propagation, late side effects, retries, and reconciliation |
| Source and status | User/course requirement, approved change, or provisional assumption; untested design versus measured result |
| Owner and review trigger | Who owns the target and what change in load, evidence, cost, or user need warrants revisiting it |

Define failures separately or use a good/total event indicator that incorporates correctness and timing. Returning a fast error must not masquerade as satisfying the successful-result requirement. A user-facing measurement can include delays invisible to server logs. See [Google SRE, implementing SLOs](https://sre.google/workbook/implementing-slos/) for event definitions and measurement choices.

If the user answers **no product SLO**, record that answer. Preserve applicable platform/course constraints and propose a provisional target only when useful. If the target is unknown, mark assumptions and uncertainty; do not invent consent. Unknown implementation measurements do not prohibit a justified design proposal, but prohibit claiming that its SLO has been demonstrated. Unknown result semantics that determine sync versus async block that final choice.

## 2. Apply product targets and SDI constraints together

The local [p99 aggregator](../../../td/core-platform/templates/p99.ts) reports duration by HTTP method and route template:

| Server p99 | SDI workshop interpretation |
|---|---|
| ≤100 ms | Target met in the supplied measurement contract |
| >100 ms and ≤350 ms | Requires justification |
| >350 ms | Outside the supplied contract |

These are **course targets, not language-selection thresholds**. `platform-compatible` broadens stack choices, not latency budgets. A product target of 500 ms does not silently waive the SDI target. If product and course targets apply to the same boundary/population, design to satisfy both; if they measure different boundaries, retain both and allocate the server share explicitly. Record an actual authorized deviation separately when required; see [waivers](derogations.md).

The script includes all usable duration samples and reports 5xx separately. It does not define every business success criterion, measure browser rendering or job completion, or fail automatically just because p99 exceeds 350 ms. Use its result for its actual scope, then add the necessary acceptance checks. Do not alter its meaning to make a proposed architecture appear compliant.

For a streaming route, inspect the actual middleware's `duration_ms` start/end events; the aggregator alone does not establish that boundary. A first-token objective cannot replace an applicable full-response-duration contract. If a long-lived stream conflicts with the course measurement contract, document and obtain any required route-specific adaptation rather than silently redefining latency.

## 3. Choose the request strategy from explicit conditions

**SLO-002 — MUST:** for each critical operation, state the applicable condition below, selected strategy, rejected alternative, consequence for the latency contract, and evidence to collect. Apply the rows to facts; do not paste a catalog into the decision.

| Observed condition / product permission | Choose this strategy | Do not choose / reason | Required check and reconsideration trigger |
|---|---|---|---|
| A bounded complete path plausibly fits the budget with headroom, with no need to wait for an external actor | Synchronous request in the simplest suitable application, usually a modular monolith | Queue or microservices solely because the target is tight: both add work and boundaries | Representative full-path test; revisit when the measured budget or capacity is exceeded |
| SQL time, N+1, lock wait, connection wait, payload size, or remote round trips dominate | Fix query shape/indexes, shorten transactions, bound results, remove unnecessary calls, and size pools within database capacity | Rewrite Python in Go/Rust: a slow SQL query or remote call remains | Trace/query evidence and the same-workload before/after test; revisit runtime only if it becomes the dominant cost |
| Independent I/O calls dominate and downstream capacity allows concurrency | Bounded concurrent I/O, cancellation, and an async-compatible client/runtime where justified | Parallel dependent operations, unbounded fan-out, or calling blocking libraries on the event loop | Dependency graph, peak downstream concurrency, errors, and end-to-end tail latency |
| Repeated expensive reads may be stale within an explicit limit | Cache, precomputation, or a maintained read projection, starting with the smallest useful mechanism | Cache authoritative permissions, balance updates, or tenant-specific results under an unsafe shared key | Freshness/invalidation/tenant rules, hit and miss latency, stampede behavior; remove or redesign when benefits disappear |
| Work exceeds the synchronous budget AND the user accepts deferred completion | Durable job acceptance + worker + status/result access; separate acceptance and completion objectives | Returning `202` without a queue/recovery design, or treating acceptance as completed work | Queue wait + execution + retries + result publication; bound backlog and test crash/retry behavior |
| Work exceeds the budget AND delayed, stale, partial, or precomputed answers are disallowed | State the feasibility conflict; investigate reducing work, improving capacity/algorithm, changing a required dependency, or changing the objective with the proper authority | Silently use a job, stream, cache, weaker validation, or fabricated fast-language promise | Demonstrate a viable complete-result path or leave the conflict unresolved |
| Work involves durable multi-step state, long human waits, compensation, or recovery across deployments | Temporal if its SDK and operating model fit; keep request acceptance and workflow outcome separate | Temporal merely because a task is slow; it does not accelerate CPU or external APIs | State transitions, retry/idempotency, versioning, task-queue delay, and business completion targets |
| The product benefits from incremental output and the client/proxy supports streaming | Streaming with first-useful-output, stall, and final-completion objectives as applicable | Claim that the first token meets a deadline for a complete usable answer | Real stream through the deployed proxy, cancellation/backpressure, output quality and final latency |
| CPU execution remains dominant after algorithm/library optimization | Compare a native/vectorized library, isolated compute worker, or measured language/runtime candidate | Change the entire stack without isolating the bottleneck; assume async makes CPU work parallel | Same algorithm/semantics/resources, realistic payloads, serialization and process-boundary cost |
| Queuing grows during bursts or sustained load | Admission control, bounded queues/concurrency, capacity planning; scale the actual bottleneck if resources allow | More workers against an already saturated shared database; an unlimited queue to hide rejection | Offered versus completed load, queue age, saturation, rejection/error policy, recovery time |
| A component needs independent capacity or fault isolation with a real ownership boundary | Consider extraction or independent deployment, accounting for added network and coordination cost | Microservices as a generic cure for a 100 ms target | Compare the complete path and operational cost before and after the boundary |

Queues absorb a burst only within capacity and completion constraints; they do not make sustained excess work disappear. The [queue-based load leveling pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling) explains the throughput tradeoff. For asynchronous acceptance, status, and terminal outcomes, see [asynchronous request–reply](https://learn.microsoft.com/en-us/azure/architecture/patterns/asynchronous-request-reply).

## 4. Allocate the budget and check feasibility

**SLO-003 — MUST:** draw the critical path before selecting performance remedies. Account for queue/pool wait, authorization, application work, SQL/dependencies, serialization, network/proxy where in scope, and headroom. Put work outside the path only if its semantics permit it; authorization and required durability cannot be removed merely to meet a time target.

For one request's serial path, elapsed stages add; independent parallel branches contribute their critical path plus coordination. **Do not add stage p99 values and call the result the end-to-end p99.** Their distributions and correlation matter. Stage allocations are planning budgets to validate with whole-request measurements.

Illustrative allocation for a **100 ms server-response budget**, not measured platform performance:

| Stage | Planned allowance |
|---|---|
| Request admission and pool waiting | 10 ms |
| Input checks and authorization | 10 ms |
| Application/domain work | 10 ms |
| SQL and necessary dependency work | 40 ms |
| Serialization and response completion | 10 ms |
| Contingency margin | 20 ms |
| Total planning envelope | 100 ms |

If measured SQL takes 180 ms in this example, investigate SQL and contention first. Even eliminating all application CPU cannot repair that path by itself. If a mandatory external call has a measured lower bound above the remaining budget, the current full-result design is infeasible; an optimistic mean is not sufficient tail-latency evidence.

For a job, plan **queue wait + all execution stages + allowed retry/backoff + result publication** against the completion objective. Include the point where the result becomes visible to the user if that is the declared boundary. A fast job submission endpoint alone says nothing about this duration.

**SLO-004 — MUST:** fit downstream attempts and backoff within the remaining deadline, leaving time to return the result or failure. Propagate cancellation where supported; do not assume a timeout rolled back an external side effect. Check connection, request, and transaction limits in the actual clients. A deadline is not authorization to retry a non-idempotent operation. Sources: [gRPC deadlines](https://grpc.io/docs/guides/deadlines/) and [AWS timeouts, retries, and backoff](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/).

## 5. Use the SLO to constrain the stack, not to invent a winner

Use the explicit comparisons in [languages and frameworks](langages-frameworks.md). Apply this order:

1. Eliminate candidates incompatible with a mandatory library, supported runtime, course profile, target environment, or required behavior.
2. Identify the critical-path cost: DB/network wait, CPU, serialization, memory/GC pressure, startup, queue wait, or a mixture. If not measured, name the hypothesis and verification plan.
3. Prefer the suitable stack the team can maintain when it plausibly fits. A Django portal is not disqualified by a 100 ms target, and FastAPI is not proven compliant by its name.
4. For I/O concurrency, verify the whole driver/library chain and bound concurrency. Async is a scheduling choice, not a promise that one query will execute faster.
5. For a measured CPU/runtime bottleneck, compare a targeted native library, worker, and appropriate runtime alternatives under equal semantics. Include interprocess/network overhead and operating cost.
6. Validate the candidate's end-to-end latency and errors under the declared envelope. Record what would trigger revisiting the framework or extracting a component.

If two candidates meet the objective, prefer the better fit for functional needs, team maintenance, simplicity, and total cost. Faster than required is not automatically more valuable than a built-in back office or an existing stable system. If neither meets it, report the conflict; do not manufacture a winner from marketing benchmarks.

## 6. Worked decisions with explicit outcomes

All numbers below are **fictional scenario inputs**, not universal thresholds, repository measurements, or waivers of the workshop contract.

| Given facts | Explicit decision | Why the alternative loses / what would change the decision |
|---|---|---|
| Python team; case-management CRUD; staff administration; fresh complete response at server p99 ≤100 ms; no long remote call; no measurements yet | Propose Django/DRF + modular API + indexed bounded Postgres access; keep the choice provisional on a representative benchmark | FastAPI remains viable, but replacing Django's administration/migration conventions adds work without evidence of a runtime bottleneck. Change if workload/library integration or measured latency favors the alternative |
| Existing Django API; search p99 420 ms against 100 ms; traces identify repeated SQL queries as the dominant cost | Fix query count, projections/indexes, and pool contention; retain Django initially | A Go rewrite leaves the same database work. Reconsider a runtime change only after SQL fixes expose a measured runtime limit |
| CSV export takes several seconds; product accepts a job; submission target p99 ≤100 ms and 99% of accepted jobs must publish a result within 30 s in the agreed workload | API + durable job + worker; size queue/concurrency to the separate 30 s objective | Holding HTTP open violates the request target. Prefer the simplest adequate durable mechanism; compare Temporal even for one task if its retries/recovery/tooling reduce implementation burden, not merely because the task is slow |
| The same export must return the complete fresh result within 100 ms; async, precomputation, and partial results are forbidden; current full path cannot fit | Declare the feasibility conflict and evaluate a bounded query/algorithm/capacity change; otherwise seek a changed requirement | A `202` would answer a different requirement. No framework is selected as a guaranteed fix without evidence |
| Dashboard reads repeat; complete response target p99 ≤100 ms; data may be 60 s old; source aggregation is too expensive per request | Start with a safe cached/precomputed projection and document freshness, tenant isolation, invalidation, misses, and rebuild cost | Full CQRS infrastructure or microservices is unnecessary if a simple projection suffices; remove the cache if fresh-per-request semantics become mandatory |
| A provider call already takes longer than a required 100 ms full AI answer; there is no authorized cached answer | Explain that the current synchronous full-answer contract is infeasible; discuss a different provider/model/workload or explicitly changed interaction | Streaming or `202` changes when the user receives the answer, not when the full answer exists. Do not count them as compliance |
| Document review waits days for a person; the submit endpoint must respond within its request target | Fast durable acceptance plus Temporal if the multi-step recovery/versioning requirements justify it; separate business approval deadlines | A bigger API instance cannot shorten human waiting. A simple persisted status plus ordinary job may suffice if the actual process lacks durable orchestration needs |
| Public content changes only on publication; delivery target includes the browser | Static/SSG output and cacheable assets; measure network and rendering, not just server handlers | Per-request SSR adds work without needed personalization. Reconsider when request-time authenticated personalization is genuinely required |

## 7. Evidence required before claiming the SLO is met

**SLO-005 — MUST:** distinguish `proposed`, `estimated`, `measured within envelope`, and `violated`. A design can be ready for review with a justified plan and unmeasured performance; it cannot be labeled performance-verified. A known infeasible requirement remains an unresolved conflict until an actual remedy or authorized change exists.

For each critical operation, specify a test that checks the declared result and boundary:

- Use representative data, payloads, permissions, dependencies, hardware limits, concurrency, and request arrivals; include warm/cold and failure paths where required.
- Measure the chosen percentile or good/total ratio and errors, sample count, test duration, throughput, saturation, and dropped/rejected work. Do not use averages or a handful of fast requests as evidence of tail performance.
- Match the load generator to the arrival model. A closed-loop test may reduce offered traffic when responses slow; report this and any dropped arrivals instead of presenting a lower-load success as capacity evidence. See [Grafana k6, open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/).
- For async flows, measure submission and actual successful completion, including queue age/retries; for streaming, measure first useful output, stalls, and completion as needed. These are distinct indicators; see [inference performance metrics](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/machine-learning/inference#inference_performance_metrics).
- Verify that timeout/cancellation bounds wasted work, retries remain within budget, and quick failures are not counted as useful successful results.
- State whether the result is a workshop acceptance run or sustained production observation. Define a review trigger for changed load, data, dependencies, runtime, or target.

Testing real integrations or paid providers still requires the scope and budget already authorized for the project; a design request does not itself authorize deployment or paid load testing. An isolated stub can test timeout behavior, but cannot prove real provider latency.

## 8. Required decision output and JSON v1 mapping

**SLO-006 — MUST:** connect each applicable SLO to an architectural consequence and validation plan in the [decision template](../assets/decision-architecture.md). For a focused comparison, a short equivalent is sufficient:

```text
Operation and required result:
Target / statistic / boundary / window / workload / failure policy:
Requirement source, or explicit absence/provisional assumption:
Selected strategy and the condition that makes it appropriate:
Rejected alternative and the condition it fails:
Latency budget and dominant cost, measured or hypothesized:
Language/framework choice and evidence still needed:
Freshness, retries, cancellation, queue/stream completion if applicable:
Added/avoided compute and operating cost:
Validation result or next test; review trigger:
```

JSON v1 deliberately has no dedicated SLO object. Use `requirements.constraints` for actual targets and deadlines, `drivers` for their priority, `assumptions` for proposed targets/envelopes, and `unknowns` for unanswered questions. Link the strategy through `architecture.rationale`, alternatives, and component rationales. Keep the full per-operation contract and evidence in the human-readable document. Do not add an unknown `slo` field, store an unapproved SLO waiver in `waivers`, or claim the validator checks latency. See [the machine-readable contract](contrat-machine.md).

The `SLO-*` rules are reviewed in the document, not by the v1 script. Sources in this reference were consulted on October 14, 2026; they support measurement and pattern properties. The concrete selection rules and fictional budgets are this skill's synthesis and must be applied to the actual project.
