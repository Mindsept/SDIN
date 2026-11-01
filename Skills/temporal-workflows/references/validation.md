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

The repository now automates extraction of both unchanged TypeScript blocks, strict type checking and nine Worker/Client tests. Run `bash ci/check-temporal.sh` from the repository root; [the test suite](../../../ci/temporal/approval.test.mjs) and its lockfile are CI-only dependencies, not application runtime dependencies. It downloads pinned packages and a disposable server, cleans its temporary workspace, and never connects to the shared platform. Linux exercises two-day waits with the time-skipping test server; macOS ARM64 uses the CLI dev server with short test inputs because the Java test server has no native ARM64 binary there. Setup failures fail the check; no silent test skips. See the [dated results and limits](../../validation-results.md).

To adapt or extend this verification in the consuming app, extract the TypeScript examples into an isolated test project. Pin one version for all Temporal packages and a supported runtime. Type-check the Workflow and Client against the real SDK. Use `@temporalio/testing` with a disposable server and Activity doubles for:

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
