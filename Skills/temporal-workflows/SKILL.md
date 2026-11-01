---
name: temporal-workflows
description: Decide whether an SDIN feature needs Temporal, then integrate only the required durable workflow, Activities and Worker. Use for durable approval, timers or multi-step recovery; a simple background job may need no workflow engine.
---

# Temporal workflows sized to the need

Start from the business operation and reuse an existing architecture decision. If the service choice is already justified, go straight to integration. A focused question needs a focused answer; do not repeat the whole architecture questionnaire.

## Choose the smallest adequate mechanism

Establish what must survive failure, what the process waits for, whether delayed completion is acceptable, and the existing processing mechanism. Ask only for missing facts that change the choice.

| Actual need | Starting point | What would justify Temporal? |
| --- | --- | --- |
| Short request or ordinary CRUD | Existing application service / transaction | A durable process spanning requests, not CRUD alone |
| One independent export, thumbnail or email with retries | Existing job mechanism; SDIN's Valkey Stream when a queue is needed | Persisted coordination between stages, durable waits or compensation |
| Simple periodic cleanup | Existing scheduler and an idempotent job | Business scheduling with durable process state and recovery requirements |
| Approval/callback over hours or days, with automatic continuation/deadline | Temporal workflow | Explain the wait and the action resumed after it |
| Several dependent external effects requiring per-step recovery | Temporal workflow | Name the recoverable steps and any actual compensation |

A job queue can also survive a restart. Duration, retries, or “enterprise” alone do not distinguish Temporal from a queue. Do not replace an adequate existing mechanism merely to consume a platform service. Under the applicable local [CCoE rule R-3-05](../CCOE-RULES.md), choose Temporal over a Stream when durable orchestration is required.

For a new choice, record briefly: need → selected mechanism → simpler alternative → operating cost → condition to reconsider. Mark Temporal and its UI N/A if unnecessary and stop Temporal integration. Use [service choices](../devops_and_choice/SKILL.md) only for an unresolved broader choice.

## Minimal integration and conditional additions

Start with the shared Temporal service, the app namespace, one task queue and one Worker process registering the needed Workflows and Activities. Reuse a compatible existing Worker. Logical separation of API, orchestration and side effects does not require separate repositories or a microservice per Activity.

| Addition | Add only when |
| --- | --- |
| App PostgreSQL database / audit record | Business queries, invariants or retention require it; Temporal's own PostgreSQL persistence does not require an app DB |
| Transactional outbox | An authoritative DB commit must reliably cause a start/signal/external message; direct Temporal commands alone need no outbox |
| Extra queue or Worker fleet | Measured resource contention, different credentials/runtime or independent scaling requires isolation |
| Compensation / saga | A completed side effect needs a defined business undo; rejection before any effect needs none |
| Heartbeat and checkpoint | An Activity is long enough to need progress recovery or cooperative cancellation; human waiting belongs in the Workflow |
| Continue-As-New / child workflows | History growth or a real lifecycle boundary warrants them; a single approval does not |
| Additional telemetry infrastructure | An operational objective cannot be met with the existing UI, logs and metrics |

Preserve deterministic workflow execution, authorized commands and retry-safe effects even in a small prototype. They are correctness properties, not optional scaling features.

## Establish the real SDIN contract

Locate the Git root; in this repository it is `../..` from this skill. Read the actual app manifests, entry points, image and pipeline plus `td/core-platform/README.md` and `td/core-platform/podman-compose.yml`. Distinguish source configuration, templates, generated build artifacts and observed runtime. A template or another skill's link does not prove a file, runner or deployment exists. Preserve the app's selected language/SDK.

- Use the app namespace and task queue consistently. Container clients on `core-network` use `temporal.internal:7233`; host clients use the published endpoint, locally `localhost:7233`. Coordinates are stored at `secret/<app>/temporal` (`address`, `namespace`). A namespace name is not an access-control credential.
- Inspect provisioning before executing it. The template `bootstrap.sh` with `TEMPORAL_NS=1` also provisions DB/S3 in its normal path; `onboard-app.sh` includes LLM setup. For Temporal alone, use/adapt the scoped namespace helper and the existing secret-writing mechanism. `temporal/ns-create.sh` only creates the namespace. Never provision unused services to make a sample work.
- For TypeScript, verify the pinned SDK's supported runtime. Prefer a supported Node LTS Worker when needed by the SDK; Bun client/build tooling and the Worker runtime are separate choices. Keep Temporal packages aligned and respect the project's stack policy. A runtime change requires adapting and testing the actual build/image.
- Determine the real workflow module or prebuilt bundle path from build outputs. Check that the final image contains it, registered Activities and compatible native SDK dependencies. Do not assume emitted `worker.js`/`workflows.js` files or a GitLab/GitHub build merely from a template. Report missing artifact evidence instead of claiming deployment compatibility.

## Implement the selected workflow

1. Define a stable business workflow ID, start-conflict/reuse policy, states, deadline origin and terminal outcomes. ID protection depends on retention/reuse policy; use durable business deduplication if the guarantee must outlive that window.
2. Keep network/DB/filesystem I/O in Activities. Workflow code uses the SDK's replay-safe primitives; use type-only imports for Activity contracts. A completed Activity result is reused during replay, but retries can execute the side effect again.
3. Choose Activity timeouts and a total retry budget from dependency latency and the business deadline. Separate transient from non-retryable errors. Make each side effect idempotent at its destination, with a stable operation key; retries may overlap after a timeout.
4. Authenticate/authorize start, status and decision commands at the app boundary. Use Signals for asynchronous decisions, Updates only for a needed synchronous business response, and Queries for read-only Workflow state. Define duplicate/late-decision behavior. If DB and Workflow both store state, choose the authority and reconciliation rule explicitly.
5. Use small reference payloads and no credentials/private documents in history. Reuse the app's logs and health endpoints; drain the Worker gracefully on SIGTERM. Readiness must reflect a Worker able to poll its configured queue, not just an open HTTP port. UI availability is not Worker readiness.
6. Size concurrency against dependency limits and memory using a representative run before adding replicas. Separate acceptance latency from completion time and human wait time. Do not turn a user wait into polling or one container per execution.
7. For deployments with open runs, test replay compatibility and choose supported versioning/patching when changes require it. A first isolated demo needs no Worker fleet migration machinery. Set closed-history retention from inspection/audit needs, separately from the maximum running duration.

Read [approval-pattern.md](references/approval-pattern.md) for a concrete, bounded approval example. For iteration and acceptance, read [validation.md](references/validation.md). Report what was inspected, type-checked, tested with doubles, or exercised against Temporal. Update the app's existing “Durable workflows” section only with applicable decisions and remaining evidence.

Sources: [TypeScript SDK/runtime](https://github.com/temporalio/sdk-typescript), [message passing](https://docs.temporal.io/develop/typescript/workflows/message-passing), [Activity failures](https://docs.temporal.io/encyclopedia/detecting-activity-failures).
