# Human approval: a small, replay-safe TypeScript pattern

Use this only when the application really has a long-running approval. The business database remains the source of truth for the request and the approver's audit record. Choose names and retention for the actual app; these are not platform-wide constants.

`workflows.ts` (the Workflow bundle must not import database or HTTP clients):

```ts
import { condition, defineSignal, proxyActivities, setHandler } from '@temporalio/workflow';

export type Outcome = 'approved' | 'rejected' | 'expired';
export type Decision = { approved: boolean; decisionId: string };
export const decide = defineSignal<[Decision]>('decide');

interface ApprovalActivities {
  finalizeOutcomeOnce(input: {
    requestId: string;
    outcome: Outcome;
    decisionId?: string;
  }): Promise<Outcome>;
}

const { finalizeOutcomeOnce } = proxyActivities<ApprovalActivities>({
  startToCloseTimeout: '30 seconds',
  retry: {
    initialInterval: '1 second',
    maximumInterval: '1 minute',
    backoffCoefficient: 2,
    maximumAttempts: 5,
  },
});

export async function approvalWorkflow(
  requestId: string,
  approvalWaitMs: number,
): Promise<Outcome> {
  let decision: Decision | undefined;
  setHandler(decide, (incoming) => {
    // Duplicate decisions do not overwrite the first accepted decision.
    if (decision === undefined) decision = incoming;
  });

  const received = await condition(() => decision !== undefined, approvalWaitMs);
  const outcome: Outcome = !received
    ? 'expired'
    : decision!.approved
      ? 'approved'
      : 'rejected';

  return await finalizeOutcomeOnce(
    received
      ? { requestId, outcome, decisionId: decision!.decisionId }
      : { requestId, outcome },
  );
}
```

The app's Worker must register an Activity named `finalizeOutcomeOnce` on the **same task queue**. For a Node ESM build that emits `worker.js` and `workflows.js` side by side, the wiring is:

```ts
import { fileURLToPath } from 'node:url';
import { NativeConnection, Worker } from '@temporalio/worker';
import { finalizeOutcomeOnce } from './activities.js';

const connection = await NativeConnection.connect({ address });
const worker = await Worker.create({
  connection,
  namespace,
  taskQueue: 'approvals',
  workflowsPath: fileURLToPath(new URL('./workflows.js', import.meta.url)),
  activities: { finalizeOutcomeOnce },
});
await worker.run();
```

Here `address` and `namespace` are loaded at boot from `secret/<app>/temporal`; adapt the emitted workflow path to the app's build. Implement the Activity as a conditional transaction in the app database: use a unique `requestId`/`decisionId` constraint, decide whether a timely recorded decision or expiry wins, persist exactly one terminal outcome, and return that *authoritative* outcome on repeats. The API must reject a decision after the persisted cutoff. If approval triggers an external call, write an outbox item in that transaction and give the downstream consumer its own idempotency key. Do not rely on Workflow replay to make an external side effect exactly once.

API-side intent (after authentication, authorization, validation, and persistence of the request/decision):

```ts
import { Client, Connection } from '@temporalio/client';

const connection = await Connection.connect({ address }); // from secret/<app>/temporal
const client = new Client({ connection, namespace });      // from the same secret

// Dispatch from the outbox if DB-to-Temporal delivery must be guaranteed.
const workflowId = `approval:${requestId}`;
const approvalWaitMs = Math.max(1, deadlineEpochMs - Date.now());
const handle = await client.workflow.start('approvalWorkflow', {
  workflowId,
  taskQueue: 'approvals',
  args: [requestId, approvalWaitMs],
});
// Persist/return handle.firstExecutionRunId where useful; do not block HTTP for approval.

// In a separate authorized decision handler, after committing the audit record:
await client.workflow.getHandle(workflowId).signal('decide', {
  approved,
  decisionId,
});
```

Here `address`, `namespace`, `requestId`, `deadlineEpochMs`, `approved`, and `decisionId` come from app configuration or a persisted request. Compute the wait from that persisted cutoff at dispatch time; the Activity's database transaction remains authoritative for a deadline race. This is a pattern, not a standalone file. A production adapter should reuse and close its connection on shutdown, reconcile ambiguous start/signal responses via workflow ID and outbox state, and handle closed runs explicitly. Only the API should grant decision authority: Temporal UI or direct gRPC access must not bypass the business authorization path.

Verification: replay must not repeat the Activity's database/external work; Activity retries may call the adapter again, so the conditional transaction and downstream idempotency are essential. Test a Worker restart while waiting, a signal arriving before the Workflow reaches `condition`, duplicate signals, expiry, and a simulated failure after the database commit.
