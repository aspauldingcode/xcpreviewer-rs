// Execute exactly the same checker module in V8; no imports or native fallback.
const fs = require('node:fs');
const assert = require('node:assert/strict');
(async () => {
  const [modulePath, output] = process.argv.slice(2);
  const module = await WebAssembly.compile(fs.readFileSync(modulePath));
  const imports = WebAssembly.Module.imports(module);
  assert.equal(imports.length, 0);
  const {verify, verify_rejected} = (await WebAssembly.instantiate(module, {})).exports;
  const rows = [];
  for (let index = 0; index < 4; ++index) {
    for (let mutation = 0; mutation < 3; ++mutation) {
      const result = verify(index, mutation) >>> 0;
      assert.equal(result, mutation ? 1 : 0);
      rows.push({case:index, mutation, mismatches:result});
    }
  }
  assert.equal(verify(4,0) >>> 0, 0xffffffff);
  assert.equal(verify(0,3) >>> 0, 0xffffffff);
  for (let index = 0; index < 10; ++index) assert.equal(verify_rejected(index), 0);
  assert.equal(verify_rejected(10) >>> 0, 0xffffffff);
  fs.writeFileSync(output, JSON.stringify({imports,rows,invalid_requests:10,checker_rejections:3,all_passed:true}));
})().catch(error => {console.error(error); process.exitCode = 1;});
