// Contract tests with a tracker double, not a live Umami/browser integration.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { trackBusinessEvent } from './track-event.mjs';

const input = { app: 'catalogue', event: 'order_created' };

test('one emission with normalized route and allowlisted properties', () => {
  const calls = [];
  const tracker = { track: (transform) => {
    calls.push(transform({ website: 'test-site', url: '/orders/private-id?token=fake',
      title: 'Private customer', referrer: '/?email=fake', data: { email: 'fake' } }));
  } };
  assert.equal(trackBusinessEvent({ ...input, tracker }), undefined);
  assert.deepEqual(calls, [{ website: 'test-site', name: 'catalogue.order_created',
    url: '/checkout/success', title: '/checkout/success', referrer: '', data: { channel: 'web' } }]);
});

test('unapproved event/app/channel never reaches the tracker', () => {
  let calls = 0;
  const tracker = { track: () => { calls++; } };
  for (const changes of [
    { app: '' }, { app: 'bad/app' }, { app: 'a'.repeat(60) },
    { event: '__proto__' }, { event: 'payment-failed' }, { channel: 'free-text-user-id' },
  ]) trackBusinessEvent({ ...input, ...changes, tracker });
  assert.equal(calls, 0);
});

test('missing tracker does not affect the business path', () => {
  for (const tracker of [undefined, null, {}, { track: false }]) {
    assert.doesNotThrow(() => trackBusinessEvent({ ...input, tracker }));
  }
});

test('synchronous tracker failure is swallowed without retry', () => {
  let calls = 0;
  const tracker = { track: () => { calls++; throw new Error('offline'); } };
  assert.doesNotThrow(() => trackBusinessEvent({ ...input, tracker }));
  assert.equal(calls, 1);
});

test('asynchronous rejection is handled without retry', async () => {
  let calls = 0;
  const tracker = { track: () => { calls++; return Promise.reject(new Error('offline')); } };
  assert.equal(trackBusinessEvent({ ...input, tracker }), undefined);
  await setImmediate();
  assert.equal(calls, 1);
});

test('an unfinished collection does not hold the caller open', () => {
  const tracker = { track: () => new Promise(() => {}) };
  assert.equal(trackBusinessEvent({ ...input, tracker }), undefined);
});
