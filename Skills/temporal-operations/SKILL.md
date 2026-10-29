---
name: temporal-operations
description: Supervise and diagnose existing SDIN Temporal workflow runs through Temporal UI, event history, and correlated Worker logs. Use for operator investigations, not for implementing new Workflow code.
---

# Temporal operations in SDIN

Temporal UI is an operator surface, not the end-user approval interface or the business database. Diagnose from an execution's recorded events before interpreting logs or changing state.

## SDIN entry points

- Local dev UI: `http://localhost:9233` (container `temporal-ui.internal:8080`). Temporal gRPC is `temporal.internal:7233` for app containers and `localhost:7233` for the host. Check `td/core-platform/README.md` for the current stack before assuming these addresses.
- Select the **app namespace** and capture `workflowId` plus `runId`. One namespace per app is the platform contract. If a run is absent, verify namespace, ID, start acknowledgment, and retention/visibility before saying it never existed.
- This repository's UI and Temporal service are dev-only and lack production auth/mTLS. Do not expose port 9233 or 7233 publicly. In a real deployment, use a secured access path and least-privilege operator roles.

## Investigation

1. Open the run and record status, start/close times, workflow type, task queue, Worker/build version if shown, and the last successful and first anomalous event. Inspect the event's failure, retry, timer, or Signal details; do not infer a root cause from `Running` alone.
2. Follow [references/diagnostic-matrix.md](references/diagnostic-matrix.md) to distinguish a normal human wait, a pending Worker task, Activity retry, Workflow Task/replay failure, and a terminal failure. Correlate with structured API/Worker logs using namespace, workflow ID, and run ID. Avoid copying secret-bearing payloads into reports or tickets.
3. Write a concise incident note: exact execution identity, event IDs/timestamps, observed state, relevant worker/queue, evidence, likely cause versus alternatives, and the safest next check. If visibility has aged out, say what evidence is missing.

Investigation is read-only by default. UI actions such as Signal, Update, cancel, terminate, reset, or retry can change or duplicate business effects. Do not perform them during a diagnosis request. For an explicitly requested intervention, first identify the exact run, expected downstream effect, Activity idempotency, approval/authorization path, and rollback plan; obtain any needed authority before acting. Human approvals should go through the app's authenticated API, not an ad hoc UI Signal.

For a new application, publish this runbook's execution identifiers and task-queue/worker mapping in its README. Use a controlled dev scenario (one waiting run and one failing Activity) to verify that the UI, event history, and Dozzle/Worker logs tell a consistent story; do not claim that test passed if the stack was not started.

Authoritative references: [Event history](https://docs.temporal.io/encyclopedia/event-history), [Visibility](https://docs.temporal.io/visibility), [Worker deployment](https://docs.temporal.io/best-practices/worker), [UI configuration](https://docs.temporal.io/references/web-ui-environment-variables).
