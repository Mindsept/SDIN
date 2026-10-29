# Iterate from observable decisions

Use a few realistic requests when changing the skill. Explain the decision and the smallest resulting integration; check for dependencies that were introduced without a need. Do not require a complete app or a running platform just to review wording.

| Request | Expected decision / scope |
| --- | --- |
| “Add a basic CRUD screen” | Existing API/DB flow; no Temporal, Worker or operator UI added |
| “Generate one export in the background; our queue retries it already” | Reuse the adequate queue; no Temporal merely for restart/retry |
| “Wait up to two days for approval, then call a provider” | One workflow, one short idempotent Activity, one queue/Worker; no app DB/outbox/saga solely for this example |
| “The existing DB transaction must commit a request and guarantee a workflow starts” | Explicit authority and transactional outbox are justified; duplicate dispatch/start handled |
| “Thousands of waiting approvals” | Distinguish waiting from runnable work; measure history/storage and active task load, not one Worker per waiting run |
| “Our compiled CI artifact changed layout” | Inspect build output and final image; adapt the real workflow bundle/module path, do not copy a template path |

A response fails the simplicity check if it provisions S3/Valkey/LLM via a broad bootstrap for Temporal alone, invents required replicas/concurrency numbers, or treats every optional pattern as an enterprise requirement.

## Check the approval code when it changes

Extract the TypeScript examples into an isolated test project (or adapt them in the consuming app). Pin one version for all Temporal packages and a supported runtime. Type-check the Workflow and Client against the real SDK. Use `@temporalio/testing` with a disposable server and Activity doubles for:

- approval → one logical effect → `completed`;
- rejection or timeout → no Activity call;
- an early Signal and duplicate/conflicting decisions → the documented first decision wins;
- duplicate start → rejected while the original run is retained;
- invalid input → terminal validation failure, not an endless Workflow Task error;
- a failure after the side effect → another Activity attempt with the same operation key; one logical effect in an idempotent double;
- replay of a captured history → no Activity side effect executed during replay.

Test actual Worker replacement, authorization, destination idempotency, cancellation and the final image in the app's integration environment before claiming those properties. A double that remembers keys does not prove the external provider or database deduplicates.

For long deadlines, use the SDK's time-skipping test server where supported. If unavailable, report that limit and use short deadlines on a disposable local server; do not change the business timeout to satisfy the test environment.

Record versions and which checks actually ran. Source type checks, Workflow tests, live destination tests and artifact startup checks establish different facts.
