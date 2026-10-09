// Local Node host only; the WASM module receives no imports or native fallback.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
(async () => {
  const [modulePath, out] = process.argv.slice(2);
  const module = await WebAssembly.compile(fs.readFileSync(modulePath));
  const imports = WebAssembly.Module.imports(module);
  assert.equal(imports.length, 0);
  const {memory, pixels, capacity, render} = (await WebAssembly.instantiate(module, {})).exports;
  assert.equal(capacity(), 204800);
  const rows = [];
  for (const [index, [w,h,stride,variant]] of [[320,160,1280,2],[320,160,1280,2],[320,160,1280,3],[3,2,16,2]].entries()) {
    const bytes = render(w,h,stride,variant);
    assert.equal(bytes,stride*h);
    fs.writeFileSync(path.join(out, `portable-${index}.rgba`), Buffer.from(new Uint8Array(memory.buffer,pixels(),bytes)));
    rows.push({index,width:w,height:h,stride,variant,bytes});
  }
  const negatives = [[0,160,1280,2],[321,160,1280,2],[320,0,1280,2],[320,161,1280,2],[320,160,1279,2],[320,160,1281,2],[320,160,1280,0],[0xffffffff,160,1280,2],[320,0xffffffff,1280,2],[320,160,0xffffffff,2]];
  const before = Buffer.from(new Uint8Array(memory.buffer,pixels(),capacity()));
  for (const args of negatives) {
    assert.equal(render(...args),0);
    assert.deepEqual(Buffer.from(new Uint8Array(memory.buffer,pixels(),capacity())),before);
  }
  fs.writeFileSync(path.join(out,'module-execution.json'),JSON.stringify({imports,exports:WebAssembly.Module.exports(module),node:process.version,v8:process.versions.v8,rows,negative_cases:negatives.length,negative_buffer_unchanged:true},null,2));
})().catch(error => { console.error(error); process.exitCode = 1; });
