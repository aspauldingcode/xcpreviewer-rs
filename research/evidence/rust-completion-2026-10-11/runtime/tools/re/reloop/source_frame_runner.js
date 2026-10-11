'use strict';
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');

async function main() {
  const [modulePath, out, widthText, heightText, strideText] = process.argv.slice(2);
  const [width, height, stride] = [widthText, heightText, strideText].map(Number);
  assert([width, height, stride].every(Number.isSafeInteger));
  assert(width >= 1 && width <= 64 && height >= 1 && height <= 64);
  assert(stride >= width * 4 && stride <= 256);
  const bytes = fs.readFileSync(modulePath);
  assert(bytes.length <= 1048576, 'Module byte limit');
  const module = await WebAssembly.compile(bytes);
  assert.equal(WebAssembly.Module.imports(module).length, 0, 'Import-free renderer required');
  assert.deepEqual(WebAssembly.Module.exports(module).map(e => [e.name, e.kind]).sort(),
    [['capacity', 'function'], ['memory', 'memory'], ['pixels', 'function'], ['render', 'function']]);
  const e = (await WebAssembly.instantiate(module, {})).exports;
  assert.equal(e.memory.buffer.byteLength, 131072, 'Fixed memory required');
  assert.equal(e.capacity(), 16384, 'Fixed allocation required');
  const pointer = e.pixels();
  assert(Number.isSafeInteger(pointer) && pointer >= 0 && pointer + 16384 <= 131072);
  const allocation = new Uint8Array(e.memory.buffer, pointer, 16384);
  allocation.fill(0xc3);
  assert.equal(e.render(stride), stride * height, 'Render extent mismatch');
  assert.equal(e.memory.buffer.byteLength, 131072, 'Memory changed');
  const frame = Buffer.from(allocation);
  for (const bad of [0, width * 4 - 1, 257, 0xffffffff]) {
    assert.equal(e.render(bad), 0, 'Invalid stride accepted');
    assert.deepEqual(Buffer.from(allocation), frame, 'Invalid render changed allocation');
  }
  fs.writeFileSync(path.join(out, 'allocation.raw'), frame);
  fs.writeFileSync(path.join(out, 'runtime.json'), JSON.stringify({
    node: process.version, v8: process.versions.v8, platform: process.platform,
    architecture: process.arch, imports: 0, memory_bytes: 131072,
    allocation_bytes: 16384, rendered_bytes: stride * height,
    invalid_requests: 4, invalid_unchanged: true
  }));
}
main().catch(error => { console.error(String(error)); process.exitCode = 1; });
