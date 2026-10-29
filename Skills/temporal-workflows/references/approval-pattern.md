# One approval, one side effect

Use after choosing Temporal for a durable human wait. This example needs one Workflow, one Activity and one Worker queue. It does not require an application database, outbox, cache, child workflow or compensation. Reuse those components only when the actual business requirements call for them.

The Workflow owns the orchestration decision. The first valid decision processed while waiting wins; duplicates and later decisions do not change it. The timeout starts when the Workflow reaches the wait, not when the HTTP request is received. For a deadline anchored to submission, pass the persisted absolute cutoff and use the SDK's replay-safe clock; define boundary races with the application's authority.

## Workflow module: workflows.ts

```ts
import {
  ApplicationFailure, condition, defineSignal, proxyActivities, setHandler,
} from '@temporalio/workflow';

export type Decision = 'approved' | 'rejected';
export type Outcome = 'completed' | 'rejected' | 'expired';
export type ApprovalInput = { requestId: string; approvalWaitMs: number };
export interface ApprovalActivities {
  executeApprovedRequest(requestId: string, operationKey: string): Promise<void>;
}
export const decide = defineSignal<[Decision]>('decide');

// Illustrative budget for a short external operation; tune to the dependency.
const { executeApprovedRequest } = proxyActivities<ApprovalActivities>({
  startToCloseTimeout: '30 seconds',
  scheduleToCloseTimeout: '2 minutes',
  retry: { initialInterval: '1 second', maximumInterval: '10 seconds', maximumAttempts: 3 },
});

export async function approvalWorkflow(input: ApprovalInput): Promise<Outcome> {
  if (
    !input || typeof input.requestId !== 'string' || input.requestId.length === 0 ||
    !Number.isSafeInteger(input.approvalWaitMs) || input.approvalWaitMs <= 0
  ) {
    throw ApplicationFailure.nonRetryable('Invalid approval input', 'InvalidInput');
  }
  let decision: Decision | undefined;
  let waiting = true;
  setHandler(decide, (incoming) => {
    if (waiting && decision === undefined &&
        (incoming === 'approved' || incoming === 'rejected')) {
      decision = incoming;
    }
  });
  const received = await condition(() => decision !== undefined, input.approvalWaitMs);
  waiting = false;
  if (!received) return 'expired';
  if (decision === 'rejected') return 'rejected';

  await executeApprovedRequest(input.requestId, `approval:${input.requestId}:execute`);
  return 'completed';
}
```

Register `executeApprovedRequest` in the Worker. Its implementation must deduplicate at the side-effect destination using `operationKey`: a provider idempotency key, or an atomic database transition when the effect itself is in that database. A local DB flag cannot make an external HTTP call atomic. An in-memory “already done” set is only a test double. On ambiguous responses, retry/reconcile using the same key. Exhausted retries fail the Workflow; approval alone does not mean the action completed.

## Client adapter: client.ts

These functions assume that the HTTP/application boundary has already validated input and authorized the actor for this request. The caller supplies a reusable configured Client and the app's queue.

```ts
import type { Client } from '@temporalio/client';
import type { ApprovalInput, Decision, approvalWorkflow } from './workflows';

export function startApproval(client: Client, taskQueue: string, input: ApprovalInput) {
  return client.workflow.start<typeof approvalWorkflow>('approvalWorkflow', {
    workflowId: `approval:${input.requestId}`,
    workflowIdReusePolicy: 'REJECT_DUPLICATE',
    workflowIdConflictPolicy: 'FAIL',
    taskQueue,
    args: [input],
  });
}

export async function sendDecision(
  client: Client, requestId: string, runId: string, decision: Decision,
): Promise<void> {
  await client.workflow.getHandle(`approval:${requestId}`, runId)
    .signal<[Decision]>('decide', decision);
}
```

Return acceptance after Temporal acknowledges start/signal; do not hold HTTP open until human approval. A Signal acknowledgment does not confirm that its decision won. Handle duplicate-start, closed-run and ambiguous transport results explicitly; return an existing handle only after checking request identity/ownership. The API derives the target run from trusted app context; it must not trust an arbitrary user-supplied workflow/run ID.

Create the Client with `Connection.connect({ address })` and `new Client({ connection, namespace })` from the app's runtime configuration. Close the shared connection on application shutdown.

## Worker and build integration

Register `approvalWorkflow` and `executeApprovedRequest` on the same task queue and namespace as the Client. An existing compatible Worker can host them.

Use `NativeConnection` and `Worker.create` with the actual Activity implementation and either a `workflowsPath` that exists in the runtime image or a supported prebuilt `workflowBundle`. Determine that path from the app's build command and artifact contents, not this reference. The Workflow import of Activity types must not pull a database/HTTP client into its sandbox. Verify native SDK dependencies for the target OS/architecture and the Worker runtime with the pinned release.

A source-level type check does not prove that the image contains the bundle or can poll the queue.

## When the example needs more

- If an existing business DB must atomically record a request/decision and guarantee delivery to Temporal, add a transactional outbox. Make the DB's decision/deadline authoritative and reconcile with the Workflow; this example's “first processed Signal wins” policy then needs adaptation.
- If approval requires durable actor audit or business listing beyond closed-history retention, use the application's existing durable records. History alone is not an unlimited business database.
- If an external action requires undo after a later failure, define that compensation. Rejection and expiry here occur before the side effect.
- Cancellation during an external call does not roll it back automatically. Specify cancellation and reconciliation according to the actual effect.

Use [validation.md](validation.md) to exercise the example. Timeouts and retry counts above are demonstration values, not platform targets.
