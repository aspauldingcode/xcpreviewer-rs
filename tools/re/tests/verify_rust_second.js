// Independent byte reader of instrumented Rust module allocations.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const base=process.argv[2],d=JSON.parse(fs.readFileSync(path.join(base,'control/result.json'))),idx=JSON.parse(fs.readFileSync(path.join(base,'rust-wasm/inputs/corpus.json')));
for(const [n,row] of d.rows.entries()) {
 const ref=idx.records[n*2],oracle=fs.readFileSync(path.join(base,'rust-wasm/inputs',ref.expected));
 const m=new WebAssembly.Module(fs.readFileSync(path.join(base,'control',row.module)));
 assert.deepEqual(WebAssembly.Module.imports(m),[]);
 assert.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function'],['verify','function']]);
 for(let mutation=0;mutation<5;mutation++) {
  const e=new WebAssembly.Instance(m,{}).exports;assert.equal(e.capacity(),16384);assert.equal(e.memory.buffer.byteLength,131072);
  const pointer=e.pixels();assert(pointer>=0 && pointer+16384<=131072);
  const target=Buffer.from(oracle),offset=mutation===1?0:mutation===2?(row.stride>row.config.width*4?row.config.width*4:0):16383;
  if(mutation>=1&&mutation<=3)target[offset]^=1;
  assert.equal(e.verify(mutation),mutation>=1&&mutation<=3?1:0);
  assert.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,pointer,16384)),target);
 }
}
console.log('verified every checker allocation');
