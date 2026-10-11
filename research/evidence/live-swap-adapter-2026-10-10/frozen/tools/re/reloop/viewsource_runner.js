const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
(async () => {
  const [jobsPath, out] = process.argv.slice(2);
  const jobs = JSON.parse(fs.readFileSync(jobsPath));
  let imports = 0, negativeRequests = 0;
  for (const job of jobs) {
    const module = await WebAssembly.compile(fs.readFileSync(job.module));
    imports += WebAssembly.Module.imports(module).length;
    assert.equal(WebAssembly.Module.imports(module).length, 0);
    const {memory, capacity, pixels, render} = (await WebAssembly.instantiate(module, {})).exports;
    assert.equal(capacity(), 204800);
    assert.equal(render(job.stride), job.stride * job.config.height);
    fs.writeFileSync(path.join(out, `pixels-${job.index}.rgba`), Buffer.from(new Uint8Array(memory.buffer, pixels(), job.stride * job.config.height)));
    const before = Buffer.from(new Uint8Array(memory.buffer, pixels(), capacity()));
    for (const stride of [0, job.config.width * 4 - 1, 1281, 0xffffffff]) {
      assert.equal(render(stride), 0);
      assert.deepEqual(Buffer.from(new Uint8Array(memory.buffer, pixels(), capacity())), before);
      negativeRequests++;
    }
  }
  fs.writeFileSync(path.join(out, 'execution.json'), JSON.stringify({imports, negative_requests: negativeRequests, invalid_buffer_unchanged: true, node: process.version, v8: process.versions.v8}, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
