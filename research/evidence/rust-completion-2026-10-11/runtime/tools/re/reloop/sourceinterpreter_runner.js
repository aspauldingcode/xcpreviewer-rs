const fs = require('node:fs');
const assert = require('node:assert/strict');
(async () => {
  const [list, result] = process.argv.slice(2);
  const rows = []; let imports = 0;
  for (const item of JSON.parse(fs.readFileSync(list))) {
    const module = await WebAssembly.compile(fs.readFileSync(item.module));
    imports += WebAssembly.Module.imports(module).length;
    assert.equal(WebAssembly.Module.imports(module).length, 0);
    const {exports} = await WebAssembly.instantiate(module, {});
    for (const fn of ['verify', 'verify_rejected']) {
      for (let argument = 0; argument <= 4; argument++) {
        const actual = exports[fn](argument) >>> 0;
        const expected = argument > 3 ? 0xffffffff : Number(fn === 'verify' && argument !== 0);
        assert.equal(actual, expected);
        rows.push({module: item.index, function: fn, argument, actual, expected, passed: actual === expected});
      }
    }
  }
  fs.writeFileSync(result, JSON.stringify({rows, imports, node: process.version, v8: process.versions.v8}, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
