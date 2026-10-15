import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';

test('portable realm: no Node globals/imports; refresh lifecycle and terminal close', {skip: typeof vm.SourceTextModule !== 'function' ? 'Requires --experimental-vm-modules' : false}, async () => {
  const source = await readFile(new URL('../index.js', import.meta.url), 'utf8');
  const context = vm.createContext({AbortController});
  let importRequests = 0;
  const denyImport = () => {importRequests++; throw Error('All imports denied');};
  const module = new vm.SourceTextModule(source, {context, importModuleDynamically: denyImport});
  await module.link(denyImport);
  await module.evaluate();
  context.createSession = module.namespace.createSession;
  const result = await vm.runInContext(`(async () => {
    function check(value, message) { if (!value) throw Error(message); }
    check(typeof process === 'undefined' && typeof Buffer === 'undefined' && typeof require === 'undefined', 'Node globals exposed');
    let builds = 0;
    const s = createSession({build: source => {builds++; return {source};}, validate: candidate => candidate.source !== 'bad'});
    check(s.status().revision === 0 && !s.frame().available, 'initial');
    await s.poll('A');
    check(s.status().revision === 1 && s.status().generation === 1, 'first publication');
    check(!(await s.poll('A')).changed && builds === 1, 'unchanged');
    await s.refresh('A'); check(builds === 2 && s.status().revision === 2, 'explicit refresh');
    try { await s.refresh('bad'); throw Error('unexpected acceptance'); } catch(e) {check(e.code === 'VALIDATION_FAILED', 'validation rejection');}
    check(s.frame().value.source === 'A' && s.status().revision === 2 && s.status().generation === 3, 'rejection retention');
    await s.refresh('good');
    check(s.status().state === 'ready' && s.status().revision === 3 && s.status().failures.length === 1, 'recovery');
    let resolve, signal;
    const late = createSession({build: (_, sig) => {signal = sig; return new Promise(r => resolve = r);}, validate: () => true});
    const pending = late.refresh('late');
    const settled = pending.then(() => {throw Error('late publication');}, e => check(e.code === 'CLOSED', 'closed result'));
    late.close(); check(signal.aborted && !late.frame().available, 'abort');
    resolve('candidate'); await settled;
    check(late.status().state === 'closed' && late.status().revision === 0 && !late.frame().available, 'terminal close');
    return {builds, revision:s.status().revision, generation:s.status().generation};
  })()`, context);
  assert.equal(importRequests,0);
  assert.equal(result.builds,4);
  assert.equal(result.revision,3);
  assert.equal(result.generation,4);
});
