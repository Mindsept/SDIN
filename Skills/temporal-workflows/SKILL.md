---
name: temporal-workflows
description: Design or implement durable Temporal workflows in an SDIN application, including its API, Worker, Activities, and human decisions. Use for application integration, not for investigating an existing run in Temporal UI.
---

# Temporal workflows in SDIN applications

Use Temporal when a business process must survive a restart, wait for a person or timer, or coordinate retried steps. For independent jobs consumed by competing workers, keep the Valkey Stream pattern. State the reason for this choice in the application README.

## Platform contract

- Inspect `td/core-platform/README.md` and the target app before changing it. This repository is a platform/template, not an already implemented business app; do not invent an app or schema.
- Use one Temporal namespace per app, not `default`. The app bootstrap with `APP=<app> TEMPORAL_NS=1` creates the namespace and writes `secret/<app>/temporal` (`address`, `namespace`). `td/core-platform/temporal/ns-create.sh` creates only the namespace, not that secret. From a container on `core-network`, the gRPC address is `temporal.internal:7233`; `localhost:7233` is host-only development. Never hard-code a dev secret into source.
- Keep API, Workflow, Activities, and Worker as distinct responsibilities. The API authenticates/authorizes commands and starts or signals a run. Workflow code decides the sequence; it never performs network, database, filesystem, or other external I/O. Activities own side effects. The Worker polls an explicitly named task queue in the app namespace.
- The template defaults to Bun for API and worker, but the Temporal TypeScript SDK officially supports Node.js for Worker features and discourages other runtimes. Use a supported Node LTS image for a production-style Temporal Worker unless a pinned SDK/Bun combination has been explicitly validated end-to-end. Do not change the API runtime merely because the Worker differs. Keep `@temporalio/*` packages on one version.

## Design and implementation

1. Define the business identity, workflow type, task queue, wait states, timeout, terminal outcomes, compensation, and source of truth before coding. Give each business request a stable workflow ID; do not treat that ID alone as permanent deduplication across closed runs and retention windows.
2. Start asynchronously from the API and return the workflow ID/run ID or a business request ID. If a database write and Temporal start/signal must be reliably coupled, persist an outbox item in the database transaction and dispatch it idempotently; a bare DB commit followed by a network call has a loss window.
3. Make every Activity retry-safe. Put an idempotency key/unique constraint or conditional state transition at the side-effect boundary; configure meaningful start-to-close timeouts and bounded retry/backoff. Use heartbeats for long-running Activities. Classify non-retryable business errors instead of retrying them forever.
4. Register Signal or Update handlers before waiting. Authenticate and authorize human decisions in the API, record the actor/audit in the app database, and keep secrets or sensitive payloads out of Temporal history. Resolve the deadline-versus-decision race in one conditional business-state transition. A Signal acknowledgment means the server accepted it, not that the business action completed. Use Updates only when the caller needs a synchronous, validated result; Queries are read-only.
5. Version workflow code so in-flight histories remain replayable. Check Worker Versioning support in the deployed server/SDK; otherwise use a documented patching or compatible-code strategy. Test replay of old histories before deploying a breaking change. Avoid unbounded histories; use Continue-As-New when a process genuinely grows without bound.
6. Keep the worker's `/health`, `/ready`, structured logs, and SIGTERM drain contract from the platform template. Readiness should mean it can poll Temporal and serve its registered task queue, not merely that an HTTP port is open.

For a concrete human-approval skeleton, read [references/approval-pattern.md](references/approval-pattern.md). Adapt its repository/side-effect boundary to the actual app; do not present the example as a ready-made business service.

## Acceptance checks

- Exercise duplicate start/decision, decision before the wait, rejection, deadline, Activity retry after a side effect, and Worker restart during a wait. Verify one business transition despite retries.
- Prove namespace/task-queue matching and that the run appears in Temporal UI. Do not claim a live integration test if the platform is not running.
- In the app README's “Durable workflows” section, document namespace, queues, workflow types, waits, compensation, why Temporal rather than a Stream, and deployment/versioning policy for in-flight runs.

Authoritative references: [Workflow replay](https://docs.temporal.io/workflows), [TypeScript SDK](https://docs.temporal.io/develop/typescript), [Worker deployment](https://docs.temporal.io/best-practices/worker), [SDK runtime support](https://github.com/temporalio/sdk-typescript).
