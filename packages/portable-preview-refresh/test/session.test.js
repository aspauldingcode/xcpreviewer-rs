import test from 'node:test';
import assert from 'node:assert/strict';
import { createSession } from '../index.js';

const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};
const code = expected => error => error.code === expected;

test('callbacks required; no implicit validation', () => {
  assert.throws(() => createSession({ build() {} }), TypeError);
});

test('poll deduplication, explicit retry, failures and recovery', async () => {
  let builds = 0;
  const session = createSession({
    build: async source => { builds++; if (source === 'B') throw Error('broken'); return source; },
    validate: async () => true,
  });
  assert.equal(session.status().state, 'idle');
  assert.deepEqual(session.frame(), { available: false, revision: 0 });
  assert.deepEqual(await session.poll('A'), { changed: true, revision: 1, generation: 1 });
  assert.equal((await session.poll('A')).changed, false);
  await session.refresh('A');
  for (let i = 0; i < 2; i++) await assert.rejects(session.refresh('B'), code('BUILD_FAILED'));
  assert.equal(builds, 4);
  assert.equal(session.status().state, 'failed');
  assert.deepEqual(session.frame(), { available: true, revision: 2, value: 'A' });
  assert.equal((await session.poll('B')).changed, false);
  await session.refresh('A');
  assert.equal(session.status().state, 'ready');
  assert.equal(session.status().generation, 5);
  assert.equal(session.status().revision, 3);
  assert.equal(session.status().failures.length, 2);
  assert.equal(session.status().failure, null);
  const snapshot = session.status(); snapshot.failures[0].code = 'changed'; snapshot.failures.length = 0;
  assert.equal(session.status().failures[0].code, 'BUILD_FAILED');
});

test('validation is awaited; false and rejection preserve accepted frame', async () => {
  const gate = deferred();
  const session = createSession({ build: async source => source, validate: async candidate => {
    if (candidate === 'wait') return gate.promise;
    if (candidate === 'false') return false;
    if (candidate === 'throw') throw Error('invalid');
    return true;
  } });
  await session.poll('A');
  const pending = session.refresh('wait');
  await Promise.resolve();
  assert.equal(session.status().state, 'building');
  assert.equal(session.frame().value, 'A');
  await assert.rejects(session.refresh('other'), code('BUSY'));
  assert.equal(session.status().generation, 2);
  gate.resolve(true);
  await pending;
  for (const source of ['false', 'throw']) await assert.rejects(session.refresh(source), code('VALIDATION_FAILED'));
  assert.equal(session.frame().value, 'wait');
  assert.equal(session.status().revision, 2);
  assert.equal(session.status().failures.length, 2);
});

test('busy build cannot be disturbed and publishes once', async () => {
  const gate = deferred(); let calls = 0;
  const session = createSession({ build: () => { calls++; return gate.promise; }, validate: () => true });
  const pending = session.poll('A');
  await assert.rejects(session.poll('B'), code('BUSY'));
  assert.equal(calls, 1);
  gate.resolve('frame'); await pending;
  assert.equal(session.status().generation, 1);
  assert.equal(session.status().revision, 1);
});

for (const phase of ['build', 'validation']) {
  for (const outcome of ['resolve', 'reject']) {
    test(`close during ${phase}, late ${outcome} cannot publish`, async () => {
      const gate = deferred(); const entered = deferred(); let signal;
      const session = createSession({
        build: (source, abortSignal) => { signal = abortSignal; if (phase === 'build') { entered.resolve(); return gate.promise; } return source; },
        validate: () => { entered.resolve(); return gate.promise; },
      });
      const pending = session.refresh('A');
      const rejection = assert.rejects(pending, code('CLOSED'));
      await entered.promise;
      session.close(); session.close();
      assert.equal(signal.aborted, true);
      assert.equal(session.status().state, 'closed');
      gate[outcome](outcome === 'resolve' ? true : Error('late'));
      await rejection;
      assert.deepEqual(session.frame(), { available: false, revision: 0 });
      assert.equal(session.status().failures.length, 0);
      await assert.rejects(session.poll('A'), code('CLOSED'));
      await assert.rejects(session.refresh('A'), code('CLOSED'));
    });
  }
}

test('close removes accepted frame and sessions remain independent', async () => {
  const options = { build: source => source, validate: () => true };
  const a = createSession(options), b = createSession(options);
  await a.refresh('😀\u0000\n');
  assert.equal(b.status().generation, 0);
  assert.equal(b.status().revision, 0);
  a.close();
  assert.deepEqual(a.frame(), { available: false, revision: 1 });
  await b.poll('B');
  assert.equal(b.frame().value, 'B');
});

test('invalid source consumes no generation', async () => {
  const session = createSession({ build: source => source, validate: () => true });
  await assert.rejects(session.poll(null), TypeError);
  assert.equal(session.status().generation, 0);
});
