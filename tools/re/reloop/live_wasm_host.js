'use strict';
// Owned primary-layer instance/frame swap policy; no native Canvas sequencing claim.
const {Worker, isMainThread, parentPort} = require('node:worker_threads');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

function request(worker, message, timeout) {
  return new Promise((resolve, reject) => {
    const finish = (error, value) => {
      clearTimeout(timer);
      worker.off('message', onMessage); worker.off('error', onError); worker.off('exit', onExit);
      error ? reject(error) : resolve(value);
    };
    const onMessage = value => value.error ? finish(new Error(value.error)) : finish(null, value);
    const onError = error => finish(error);
    const onExit = code => finish(new Error('Candidate worker exited: ' + code));
    const timer = setTimeout(() => finish(new Error('Candidate deadline exceeded')), timeout);
    worker.once('message', onMessage); worker.once('error', onError); worker.once('exit', onExit);
    worker.postMessage(message);
  });
}

class LiveWasmHost {
  #active = null; #busy = false; #closed = false; #revision = 0;
  snapshot() {
    if (!this.#active) return null;
    const {revision, token, frame, moduleSha256} = this.#active;
    return {revision, token, moduleSha256, frame: Buffer.from(frame)};
  }
  async propose(moduleBytes, expected, width, height, stride, timeout = 1500) {
    assert(!this.#closed && !this.#busy, 'Host closed or proposal already active');
    assert(Buffer.isBuffer(moduleBytes) && moduleBytes.length <= 1048576);
    assert(Buffer.isBuffer(expected) && expected.length === 16384);
    assert([width, height, stride, timeout].every(Number.isSafeInteger));
    assert(width >= 1 && width <= 64 && height >= 1 && height <= 64);
    assert(stride >= width * 4 && stride <= 256 && timeout >= 50 && timeout <= 5000);
    // Capture immutable proposal bytes before asynchronous work.
    const proposal = Buffer.from(moduleBytes), prediction = Buffer.from(expected);
    this.#busy = true;
    const candidate = new Worker(__filename, {resourceLimits: {maxOldGenerationSizeMb: 64}});
    let committed = false;
    try {
      const value = await request(candidate, {module: proposal, width, height, stride}, timeout);
      const frame = Buffer.from(value.frame);
      assert.deepEqual(frame, prediction, 'Complete allocation differs from independent expectation');
      assert(!this.#closed, 'Host closed during proposal');
      const old = this.#active;
      this.#active = {worker: candidate, frame, revision: ++this.#revision,
        token: crypto.randomUUID(), moduleSha256: crypto.createHash('sha256').update(proposal).digest('hex')};
      committed = true;
      if (old) await old.worker.terminate();
      return this.snapshot();
    } finally {
      if (!committed) await candidate.terminate();
      this.#busy = false;
    }
  }
  async verifyLive(timeout = 1500) {
    assert(this.#active && !this.#busy && !this.#closed);
    assert(Number.isSafeInteger(timeout) && timeout >= 50 && timeout <= 5000);
    this.#busy = true;
    try {
      const result = await request(this.#active.worker, {read: true}, timeout);
      assert.deepEqual(Buffer.from(result.frame), this.#active.frame);
      return this.snapshot();
    } finally { this.#busy = false; }
  }
  async close() {
    this.#closed = true;
    const old = this.#active; this.#active = null;
    if (old) await old.worker.terminate();
  }
}

if (isMainThread) module.exports = {LiveWasmHost};
else {
  let active;
  parentPort.on('message', async message => {
    try {
      if (message.read) {
        assert(active, 'No active instance');
        assert.equal(active.e.memory.buffer.byteLength, 131072);
        assert.equal(active.e.pixels(), active.pointer);
        parentPort.postMessage({frame: Buffer.from(new Uint8Array(active.e.memory.buffer, active.pointer, 16384))});
        return;
      }
      assert(!active, 'Worker accepts only one module');
      const module = await WebAssembly.compile(message.module);
      assert.equal(WebAssembly.Module.imports(module).length, 0);
      assert.deepEqual(WebAssembly.Module.exports(module).map(e => [e.name, e.kind]).sort(),
        [['capacity', 'function'], ['memory', 'memory'], ['pixels', 'function'], ['render', 'function']]);
      const e = (await WebAssembly.instantiate(module, {})).exports;
      assert.equal(e.memory.buffer.byteLength, 131072);
      assert.equal(e.capacity(), 16384);
      const pointer = e.pixels();
      assert(Number.isSafeInteger(pointer) && pointer >= 0 && pointer + 16384 <= 131072);
      const allocation = new Uint8Array(e.memory.buffer, pointer, 16384);
      allocation.fill(0xc3);
      assert.equal(e.render(message.stride), message.stride * message.height);
      assert.equal(e.memory.buffer.byteLength, 131072);
      assert.equal(e.pixels(), pointer);
      const frame = Buffer.from(allocation);
      for (const bad of [0, message.width * 4 - 1, 257, 0xffffffff]) {
        assert.equal(e.render(bad), 0);
        assert.deepEqual(Buffer.from(allocation), frame);
        assert.equal(e.memory.buffer.byteLength, 131072);
      }
      active = {e, pointer};
      parentPort.postMessage({frame});
    } catch (error) { parentPort.postMessage({error: String(error)}); }
  });
}
