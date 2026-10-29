# Deterministic investigation of a Temporal execution

Start with the tuple `(namespace, workflowId, runId)`. Open the execution in `http://localhost:9233` on the local SDIN stack. Keep `runId` when a workflow has retried, reset, or continued as new; a workflow ID alone may describe more than one run over time. Inspect status and chronological event history before reading potentially noisy logs.

| Evidence in the run | Interpretation to test | Read-only next check |
| --- | --- | --- |
| `Running`, timer started, no failure; or waiting after a registered human-decision point | May be healthy waiting, not stuck | Check deadline, timer/signal events, app decision/outbox state, and whether the UI's last event matches the expected wait. |
| `WorkflowExecutionStarted` / task scheduled, but no Workflow Task completion | No polling Worker, wrong namespace/queue, or Worker cannot load workflow type | Compare the run's task queue with the deployed Worker config and `/ready`; inspect `<app>-worker` logs. |
| Activity scheduled but not started | Activity Worker not polling that queue or saturated | Check queue routing, Worker readiness/capacity, and schedule-to-start latency if metrics exist. |
| Activity started, repeated `ActivityTaskFailed` or timeout, retry scheduled | External dependency, timeout, or retry policy problem | Read failure type and attempt count; inspect matching Worker logs and downstream service. Confirm idempotency before any manual retry. |
| Repeated `WorkflowTaskFailed` after deployment | Code/replay incompatibility or missing workflow/handler is possible | Read the exact failure and stack; compare deployed build with the run's history and versioning policy. Do not reset just to hide a nondeterminism error. |
| `WorkflowExecutionSignaled`, but no expected follow-up | Signal was accepted, not necessarily processed | Check whether a Worker processed a later Workflow Task, the handler name/version, and the app's persisted approval state. |
| `Failed`, `Canceled`, `Terminated`, or `TimedOut` | Terminal outcome; recovery semantics differ | Identify the terminal event and preceding failure. Explain whether restart creates a new run or duplicates effects before proposing action. |
| UI cannot load any namespace/run | UI/service/network issue, not proof that workflows failed | Check `podman ps`, then `podman logs --tail 100 temporal-ui.internal` and `podman logs --tail 100 temporal.internal`; redact payloads. |

For an app Worker in the local stack, `podman logs --tail 100 <app>-worker` is read-only; substitute the actual container name from the app compose file. Dozzle at `http://localhost:9999` is an alternative log view. If no containers are running, report that the live diagnosis could not be verified, rather than fabricate an execution state.

Use this report shape so a teammate can reproduce the conclusion:

```text
Namespace / workflowId / runId:
Status and observation time:
Last expected event (ID + time):
First anomalous or missing transition:
Workflow type / task queue / Worker build:
Correlated log or metric (redacted):
Observed fact vs hypothesis:
Next read-only check or proposed authorized intervention:
```

Do not paste raw Activity inputs/outputs by default: Temporal history may hold secrets or personal data. A business-state repair belongs to the owning application; an operator UI action does not replace its audit and authorization model.
