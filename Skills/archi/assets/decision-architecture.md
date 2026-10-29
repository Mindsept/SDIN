# Architecture decision — [project name]

Date: [review date] · Status: [draft / ready for review] · Owner: [actual person or unassigned]
Policy: [strict-typescript / platform-compatible] · Context: [workshop / intended production / to be clarified]

## Need and scope

[Actors, expected outcome, happy path, important error, excluded features.]

## Known facts and clarifications

| Decisive question | Answer / source | Possible assumption | Which decision is blocked? |
|---|---|---|---|
| [question] | [answer or unknown] | [explicit assumption] | [decision or none] |

## Response-time SLOs and result semantics

[Ask whether an SLO or maximum response time exists. If none, record that explicit answer, applicable course targets, and any proposed assumption. Distinguish a hard deadline from a percentile target. One row per critical operation; separate job acceptance/completion and first useful streamed output/final output where relevant.]

| Operation and start/end boundary | Required result / execution semantics | Target, statistic, and window | Workload / payload / resources | Success, failures, freshness, deadline behavior | Source and evidence status |
|---|---|---|---|---|---|
| [route/journey; measured from…to…] | [complete result / durable job acceptance / first useful output / finished job] | [e.g. p99 ≤…ms; window; separate client deadline] | [arrival rate/burst, concurrency, data size, cold/warm conditions] | [errors/rejections/cancellations, permitted staleness, timeout effect] | [user/course/assumption; proposed/estimated/measured within envelope/violated] |

| Operation | Critical path and budget allocation | Selected strategy and enabling condition | Rejected strategy and reason | Evidence / next test | Review trigger |
|---|---|---|---|---|---|
| [same operation] | [queue/pool, auth, application, DB/dependency, serialization/network, margin; allocations are not additive p99 estimates] | [sync / bounded I/O / cache or projection / job / durable workflow / stream; required permission or fact] | [why the nearest option fails the actual contract] | [representative test and actual result, or not measured] | [load, latency, freshness, dependency or requirement change] |

Feasibility conflicts: [none, or the incompatible requirement and evidence; do not replace complete results with `202` or first tokens without agreement].
SLO ownership and changes: [actual owner/authority, source, any approved change; no fabricated approval].

## Decisions and alternatives

| Decision | Selected option | Project conditions satisfied / evidence | Nearest alternative and condition it fails | SLO effect / validation needed | Compute avoided or cost accepted | Reassess if… |
|---|---|---|---|---|---|---|
| Topology / internal pattern / execution mode | [separate choices; compatible patterns may coexist] | [applied decision rule] | [plausible option and actual reason] | [critical-path effect; evidence] | [concrete cost or to be measured] | [trigger] |
| Language / runtime | [per component] | [applied language comparison] | [option and actual reason] | [bottleneck/constraint, not a generic speed claim] | [cost] | [trigger] |
| Framework | [choice or none] | [applied framework comparison] | [option and actual reason] | [functional fit and representative test] | [cost] | [trigger] |
| Data access | [ORM / builder / SQL / N/A] | [queries, transactions, team] | [option and actual reason] | [query/transaction/pool budget] | [cost] | [trigger] |

## Components and flows

[Deployment units, browser/API/worker boundaries, data ownership, and flows. Include a diagram only if it clarifies the result. Do not draw a service that was not selected.]

## Code structure

[Concrete directory tree per component, test and migration directories; no mandatory empty directories.]

Use-case path: [transport → application → domain/adapter, validation, authorization, transaction, error].
Dependency constraints: [allowed/forbidden imports and applicable language-specific check].

## Services and provisioning

| SDI service | Used by | Resource / secret / endpoint | Need addressed or N/A reason | Provisioning / validation |
|---|---|---|---|---|
| [service] | [component] | [identifiers without secret values] | [reason] | [owner and evidence] |

Ports: [block checked for collisions, or unassigned].
Template adaptations: [CI commands, images, SDKs, bootstrap, analytics proxy, vector extension, others].

## Data and contracts

[Logical schema/ownership, migrations, transactions, access rights/tenant, files, and retention.]
[APIs/events/jobs: errors, compatibility, timeouts, idempotency, retries, cancellation, recovery.]

## Quality attributes and evidence

| Area | Requirement / budget | Planned or executed validation | Result / limitation | Owner |
|---|---|---|---|---|
| [security, performance, tests, operations, costs…] | [target or justified N/A] | [method] | [observed / to be checked] | [actual person or to be assigned] |

## Waivers

[None, or links to proposals/decisions with rule, scope, evidence, authority, dates, and exit plan. Never write "approved" without actual approval.]

## Implementation and review

[Minimum steps, validation, migration/rollback if needed, review trigger.]

## Validation status

Machine-readable contract: [command, date, exit code, and actual results, or not run].
Responsibility review: [evidence and limitations].
Integrations / load: [actually tested or not].
SLO verification: [per operation: proposed/estimated/measured within envelope/violated; target versus result and test scope. JSON validation is not latency verification].
Remaining blocking unknowns: [list or none].

## Sources

[Local files/lines and official documentation consulted; date and versions actually verified.]
