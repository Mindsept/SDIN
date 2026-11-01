import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import { after, before, test } from 'node:test';
import { setTimeout as delay } from 'node:timers/promises';
import { TestWorkflowEnvironment } from '@temporalio/testing';
import { Worker, Runtime, DefaultLogger, bundleWorkflowCode } from '@temporalio/worker';
import { startApproval, sendDecision } from './lib/client.js';

const require = createRequire(import.meta.url);
let environment;
let workflowBundle;
const calls = new Map();
const effects = new Set();
let approvedHistory;
// Use the full CLI dev server for SDK behavior, including Worker replacement.
// The Java time-skipping server is limited to the long-timer case below.
const waitMs = 500;

before(async () => {
  Runtime.install({ logger: new DefaultLogger('ERROR') });
  environment = await TestWorkflowEnvironment.createLocal({ server: {
    ip: '127.0.0.1', ui: false, executable: { type: 'cached-download', version: 'v1.9.1' },
  } });
  console.log('Temporal SDK 1.25.0; CLI 1.9.1, bounded real-time cases');
  workflowBundle = await bundleWorkflowCode({ workflowsPath: require.resolve('./lib/workflows.js') });
}, { timeout: 120_000 });

after(async () => { await environment?.teardown(); });

async function newWorker(taskQueue) {
  return Worker.create({
    connection: environment.nativeConnection,
    taskQueue,
    workflowBundle,
    activities: {
      async executeApprovedRequest(requestId, operationKey) {
        const attempts = calls.get(requestId) ?? [];
        attempts.push(operationKey);
        calls.set(requestId, attempts);
        effects.add(operationKey); // Destination double deduplicates atomically.
        if (requestId === 'retry' && attempts.length === 1) {
          throw new Error('Ambiguous response after the effect');
        }
        if (requestId === 'exhausted') throw new Error('Destination unavailable');
      },
    },
  });
}

async function start(requestId, approvalWaitMs = waitMs) {
  const taskQueue = `approval-test-${randomUUID()}`;
  const handle = await startApproval(environment.client, taskQueue, { requestId, approvalWaitMs });
  return { taskQueue, handle };
}

async function decide(requestId, handle, decision) {
  await sendDecision(environment.client, requestId, handle.firstExecutionRunId, decision);
}

async function result(taskQueue, handle) {
  const worker = await newWorker(taskQueue);
  return worker.runUntil(() => handle.result());
}

test('early and conflicting Signals: first valid approval wins, one effect', { timeout: 20_000 }, async () => {
  const { taskQueue, handle } = await start('approved');
  // All Signals arrive before any Worker polls the queue.
  await handle.signal('decide', 'invalid');
  await decide('approved', handle, 'approved');
  await decide('approved', handle, 'rejected');
  await decide('approved', handle, 'approved');
  assert.equal(await result(taskQueue, handle), 'completed');
  assert.deepEqual(calls.get('approved'), ['approval:approved:execute']);
  approvedHistory = await handle.fetchHistory();
});

test('rejection wins over a later approval and executes no Activity', { timeout: 20_000 }, async () => {
  const { taskQueue, handle } = await start('rejected');
  await decide('rejected', handle, 'rejected');
  await decide('rejected', handle, 'approved');
  assert.equal(await result(taskQueue, handle), 'rejected');
  assert.equal(calls.has('rejected'), false);
});

test('deadline expires without an Activity', { timeout: 20_000 }, async () => {
  const { taskQueue, handle } = await start('expired');
  assert.equal(await result(taskQueue, handle), 'expired');
  assert.equal(calls.has('expired'), false);
});

test('duplicate start is rejected both while running and after completion', { timeout: 20_000 }, async () => {
  const { taskQueue, handle } = await start('duplicate');
  const duplicateStart = () => startApproval(environment.client, taskQueue, {
    requestId: 'duplicate', approvalWaitMs: waitMs,
  });
  const alreadyStarted = { name: 'WorkflowExecutionAlreadyStartedError' };
  await assert.rejects(duplicateStart, alreadyStarted);
  await decide('duplicate', handle, 'approved');
  assert.equal(await result(taskQueue, handle), 'completed');
  await assert.rejects(duplicateStart, alreadyStarted);
  assert.equal(calls.get('duplicate').length, 1);
});

test('invalid input is a terminal validation failure', { timeout: 20_000 }, async () => {
  const { taskQueue, handle } = await start('invalid', 0);
  await assert.rejects(() => result(taskQueue, handle), (error) => {
    assert.equal(error.name, 'WorkflowFailedError');
    assert.equal(error.cause.type, 'InvalidInput');
    assert.equal(error.cause.nonRetryable, true);
    return true;
  });
  assert.equal((await handle.describe()).status.name, 'FAILED');
  assert.equal(calls.has('invalid'), false);
});

test('retry after a side effect reuses its key: two attempts, one logical effect', { timeout: 20_000 }, async () => {
  const { taskQueue, handle } = await start('retry');
  await decide('retry', handle, 'approved');
  assert.equal(await result(taskQueue, handle), 'completed');
  assert.deepEqual(calls.get('retry'), ['approval:retry:execute', 'approval:retry:execute']);
  assert.equal([...effects].filter((key) => key === 'approval:retry:execute').length, 1);
});

test('exhausted retries fail the Workflow after the configured three attempts', { timeout: 20_000 }, async () => {
  const { taskQueue, handle } = await start('exhausted');
  await decide('exhausted', handle, 'approved');
  await assert.rejects(() => result(taskQueue, handle), { name: 'WorkflowFailedError' });
  assert.equal(calls.get('exhausted').length, 3);
  assert.equal((await handle.describe()).status.name, 'FAILED');
});

test('Worker replacement resumes the existing durable wait', { timeout: 20_000 }, async () => {
  const { taskQueue, handle } = await start('replacement', 60_000);
  const first = await newWorker(taskQueue);
  await first.runUntil(async () => {
    const deadline = Date.now() + 5_000;
    while (!(await handle.fetchHistory()).events.some((event) => event.timerStartedEventAttributes)) {
      assert.ok(Date.now() < deadline, 'Workflow did not reach its durable timer');
      await delay(25);
    }
  });
  assert.equal((await handle.describe()).status.name, 'RUNNING');
  await decide('replacement', handle, 'approved');
  assert.equal(await result(taskQueue, handle), 'completed');
  assert.equal(calls.get('replacement').length, 1);
});

test('captured history replays without executing another Activity', { timeout: 20_000 }, async () => {
  assert.ok(approvedHistory?.events.some((event) => event.activityTaskCompletedEventAttributes));
  const beforeReplay = JSON.stringify([...calls]);
  await Worker.runReplayHistory({ workflowBundle }, approvedHistory);
  assert.equal(JSON.stringify([...calls]), beforeReplay);
});

// Time skipping is global: use its own environment and no parallel tests.
// No ARM64 macOS binary exists; the nine full-server cases above still run there.
if (process.platform === 'linux' && process.arch === 'x64') {
  test('two-day approval deadline expires on an isolated time-skipping server', { timeout: 30_000 }, async () => {
    const timers = await TestWorkflowEnvironment.createTimeSkipping({ server: {
      executable: { type: 'cached-download', version: 'v1.40.0' },
    } });
    try {
      let activityCalls = 0;
      const taskQueue = `approval-timer-${randomUUID()}`;
      const worker = await Worker.create({
        connection: timers.nativeConnection, taskQueue, workflowBundle,
        activities: { executeApprovedRequest: async () => { activityCalls++; } },
      });
      const handle = await startApproval(timers.client, taskQueue, {
        requestId: 'two-day-timeout', approvalWaitMs: 2 * 24 * 60 * 60 * 1000,
      });
      assert.equal(await worker.runUntil(() => handle.result()), 'expired');
      assert.equal(activityCalls, 0);
    } finally {
      await timers.teardown();
    }
  });
}
