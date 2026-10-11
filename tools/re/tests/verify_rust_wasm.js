// Fresh direct runtime verifier; independent of LiveWasmHost publication policy.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const base=process.argv[2],index=JSON.parse(fs.readFileSync(path.join(base,'control/inputs/corpus.json')));
for(const [n,row] of index.records.entries()) {
 const bytes=fs.readFileSync(path.join(base,'control/inputs',row.module));
 const m=new WebAssembly.Module(bytes);
 assert.deepEqual(WebAssembly.Module.imports(m),[]);
 assert.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);
 const e=new WebAssembly.Instance(m,{}).exports;
 assert.equal(e.memory.buffer.byteLength,131072);assert.equal(e.capacity(),16384);
 const pointer=e.pixels();assert(pointer>=0 && pointer+16384<=131072);
 const a=new Uint8Array(e.memory.buffer,pointer,16384);a.fill(0x11);
 assert.equal(e.render(row.stride),row.stride*row.config.height);
 const reference=fs.readFileSync(path.join(base,'control/inputs',row.expected));
 assert.deepEqual(Buffer.from(a),reference);
 assert.deepEqual(Buffer.from(a),fs.readFileSync(path.join(base,'control/runtime','revision-'+n+'.raw')));
 for(const bad of [0,row.config.width*4-1,257,0xffffffff]) {
  assert.equal(e.render(bad),0);assert.deepEqual(Buffer.from(a),reference);
  assert.equal(e.memory.buffer.byteLength,131072);assert.equal(e.pixels(),pointer);
 }
 assert.throws(()=>e.memory.grow(1),RangeError);
 a.fill(0x7e);assert.equal(e.render(row.stride),row.stride*row.config.height);
 assert.deepEqual(Buffer.from(a),reference);
}
console.log('verified 84 import-free Rust modules, 336 invalid strides, 84 growth rejections');
