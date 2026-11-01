# Bounded diagnosis of one execution

Begin with environment + namespace + workflow ID + run ID. Confirm the UI endpoint from the deployment; the SDIN host default is `http://localhost:9233`. Read status, pending Activities and the relevant history interval. History can omit intermediate Activity retry events: use pending retry/last-failure details and logs before concluding that only one attempt occurred.

| Observed evidence | Interpretation to test | Next observation / stopping condition |
| --- | --- | --- |
| `Running`, expected human wait or unexpired timer, no failure | Normal durable wait | Compare the app's deadline and received Signals. If consistent, report “waiting as designed” and stop; do not reset or scale. |
| Workflow Task scheduled, no completion | Worker absent, wrong queue/namespace, capacity issue or task failure | Compare actual polling/configuration and the deployed workflow type; inspect the relevant Worker log. A health port alone proves little. |
| Activity pending, no start | Routing, capacity or rate limitation | Check queue/pollers, schedule-to-start latency and downstream budget. Do not add replicas before distinguishing missing workers from saturation. |
| Pending Activity retry, last failure or timeout | Dependency or retry-budget problem | Inspect failure type, attempt and timeout kind. Distinguish schedule-to-start, start-to-close, schedule-to-close and heartbeat failures; do not merely increase all timeouts. |
| Repeated `WorkflowTaskFailed` after a release | Replay/code incompatibility is possible | Read the precise error and compare actual Worker artifact/version with history. A template build path is not evidence of the deployed artifact. |
| `WorkflowExecutionSignaled`, no expected transition | Accepted Signal may be unprocessed, ignored or too late | Check a subsequent Workflow Task, handler contract, decision/deadline policy and authoritative app state if present. Do not send duplicates blindly. |
| Failed, Canceled, Terminated or TimedOut | Different terminal outcomes | Inspect the terminal event and causal failure; establish whether intervention repeats effects or needs business reconciliation. |
| UI unavailable | UI or access problem may be independent of execution | Check the UI and service reachability separately; use an available Client/CLI to describe the run. Do not restart workflows based on UI failure. |
| Run missing | Wrong environment/namespace/ID, filters, visibility delay or expired closed history | Check those facts and app start acknowledgment. State missing evidence; do not claim it never ran. |

Use bounded logs from observed container names. Local examples:

```sh
podman ps
podman logs --tail 100 temporal-ui.internal
podman logs --tail 100 temporal.internal
```

Read the app Worker's actual name in its Compose/deployment configuration before requesting its logs. Dozzle at `http://localhost:9999` is an alternative if already available. CLI syntax depends on the installed version; check help rather than mixing legacy `tctl` flags with the `temporal` CLI. SDIN's `lib/temporal.sh` defines a wrapper named `tctl` around the modern CLI.

For a routine check, return the execution identity, observed wait/error, evidence and next step in a few lines. For an incident that needs handoff, expand only the useful fields:

```text
Environment / namespace / workflowId / runId:
Observation time and expected deadline:
Decisive event ID or pending Activity details:
Task queue / Worker build / relevant redacted log:
Observed fact / likely cause / remaining uncertainty:
Authorized action or next observation:
```

## Practice the stopping conditions

- Approval started two hours ago, deadline tomorrow, no decision received: expected wait; no repair, polling loop or new alert stack.
- UI is down while an authorized Client confirms the Workflow is progressing: diagnose UI access/service; do not fail business readiness or restart the Workflow.
- Activity has retried but no per-attempt failure events appear: inspect pending attempt/last failure and Worker logs; do not infer exactly one execution.
- A task queue has no matching poller: verify deployment/queue configuration before proposing scale-out.
- An operator asks “why is this stuck?”: conclude from evidence; resetting, signaling approval or terminating is not part of that diagnosis request.

These are evaluation scenarios, not a claim that live incidents were reproduced.
