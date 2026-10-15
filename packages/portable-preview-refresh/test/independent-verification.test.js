import test from 'node:test';
import assert from 'node:assert/strict';
import {createSession, RefreshError} from '../index.js';
const rejects = code => e => e instanceof RefreshError && e.code === code;
const gate = () => { let resolve, reject; const promise = new Promise((a,b) => {resolve=a; reject=b;}); return {promise,resolve,reject}; };

test('independent: synchronous build and validator reentrancy cannot consume generations', async () => {
  const nested = []; let s;
  s = createSession({build(source) {
    assert.equal(s.status().state, 'building');
    nested.push(assert.rejects(s.refresh('nested-build'), rejects('BUSY')));
    return source;
  }, validate() {
    nested.push(assert.rejects(s.poll('nested-validation'), rejects('BUSY')));
    return true;
  }});
  await s.poll('A'); await Promise.all(nested);
  assert.equal(s.status().generation, 1);
  assert.equal(s.status().revision, 1);
  assert.equal((await s.poll('A')).changed, false);
});

test('independent: busy rejection preserves observed source and original failing attempt', async () => {
  const g = gate(); let calls = 0;
  const s = createSession({build(source) { calls++; return calls === 1 ? g.promise : source; }, validate: () => true});
  const pending = s.poll('A');
  const failure = assert.rejects(pending, rejects('BUILD_FAILED'));
  await assert.rejects(s.poll('B'), rejects('BUSY'));
  g.reject(new Error('original failure')); await failure;
  assert.equal(s.status().failures.length, 1);
  assert.equal(s.status().generation, 1);
  assert.equal((await s.poll('A')).changed, false);
  assert.equal((await s.poll('B')).generation, 2);
});

test('independent: async validation gates publication and rejects truthy nonboolean', async () => {
  const g = gate(); let validating;
  const s = createSession({build: source => source, validate: candidate => candidate === 'new' ? (validating = true, g.promise) : true});
  await s.refresh('old');
  const pending = s.refresh('new');
  const failure = assert.rejects(pending, rejects('VALIDATION_FAILED'));
  await Promise.resolve(); assert.equal(validating, true);
  assert.deepEqual(s.frame(), {available:true, revision:1, value:'old'});
  await assert.rejects(s.refresh('other'), rejects('BUSY'));
  g.resolve('truthy'); await failure;
  assert.equal(s.frame().value, 'old');
  assert.equal(s.status().revision, 1);
  assert.equal(s.status().failures[0].stage, 'validation');
});

for (const phase of ['build', 'validate']) for (const rejectLate of [false,true]) {
  test(`independent: synchronous close from ${phase}; late ${rejectLate ? 'rejection' : 'completion'}`, async () => {
    const g = gate(); let signal; let s;
    const callback = (_value, abortSignal) => { signal = abortSignal; s.close(); return g.promise; };
    s = createSession({build: phase === 'build' ? callback : x => x,
      validate: phase === 'validate' ? (candidate, source, abortSignal) => callback(candidate, abortSignal) : () => {assert.fail('validation after build closed');}});
    const p = s.refresh('A'); const done = assert.rejects(p, rejects('CLOSED'));
    await Promise.resolve();
    assert.equal(signal.aborted, true);
    if (rejectLate) g.reject(Error('late')); else g.resolve(true);
    await done;
    assert.equal(s.status().state, 'closed'); assert.equal(s.status().revision, 0);
    assert.equal(s.status().failures.length, 0);
    assert.equal(s.frame().available, false);
  });
}

test('independent: snapshots isolate bookkeeping; candidate remains documented caller-owned reference', async () => {
  const candidate = {pixels: [1]}; let fail = false;
  const s = createSession({build: () => {if(fail) throw Error('x'); return candidate;}, validate: () => true});
  await s.refresh('A'); fail=true;
  await assert.rejects(s.refresh('B'), rejects('BUILD_FAILED'));
  const status = s.status(); status.failure.code='X'; status.failures[0].generation=999; status.revision=999;
  const frame = s.frame(); frame.revision=999; frame.available=false; frame.value.pixels[0]=2;
  assert.equal(s.status().failure.code, 'BUILD_FAILED');
  assert.equal(s.status().failures[0].generation,2); assert.equal(s.status().revision,1);
  assert.equal(s.frame().available,true); assert.equal(s.frame().value,candidate);
  assert.equal(s.frame().value.pixels[0],2);
});
