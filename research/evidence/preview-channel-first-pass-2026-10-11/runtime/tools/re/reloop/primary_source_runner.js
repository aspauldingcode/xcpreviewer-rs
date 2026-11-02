const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const [out,mode,index]=process.argv.slice(2),jobs=JSON.parse(fs.readFileSync(path.join(out,'jobs.json')));
 if(mode==='checker'){
  const module=await WebAssembly.compile(fs.readFileSync(path.join(out,`checker-${index}.wasm`)));assert.equal(WebAssembly.Module.imports(module).length,0);
  const e=(await WebAssembly.instantiate(module,{})).exports,rows=[];
  for(let s=0;s<2;s++)for(let m=0;m<5;m++){const count=e.verify(s,m);assert.equal(count,m?1:0);rows.push({stride_index:s,mutation:m,count});}
  assert.equal(e.verify_all(),8);fs.writeFileSync(path.join(out,`checker-v8-${index}.json`),JSON.stringify(rows));return;
 }
 const rows=[],invalid=[];
 for(const job of jobs){
  const module=await WebAssembly.compile(fs.readFileSync(job.module));assert.equal(WebAssembly.Module.imports(module).length,0);
  for(let s=0;s<2;s++)for(let repeat=0;repeat<2;repeat++){
   const e=(await WebAssembly.instantiate(module,{})).exports;assert.equal(e.capacity(),16384);const bytes=new Uint8Array(e.memory.buffer,e.pixels(),16384);bytes.fill(0xc3);
   assert.equal(e.render(job.strides[s]),job.strides[s]*job.config.height);
   fs.writeFileSync(path.join(out,`frame-${job.index}-${s}-${repeat}.raw`),Buffer.from(bytes));rows.push({job:job.index,stride_index:s,repeat});
  }
  const e=(await WebAssembly.instantiate(module,{})).exports,bytes=new Uint8Array(e.memory.buffer,e.pixels(),16384);bytes.fill(0xc3);assert.equal(e.render(job.strides[0]),job.strides[0]*job.config.height);const before=Buffer.from(bytes);
  for(const [k,stride] of [0,job.config.width*4-1,257,0xffffffff].entries()){
   assert.equal(e.render(stride),0);assert.deepEqual(Buffer.from(bytes),before);fs.writeFileSync(path.join(out,`invalid-${job.index}-${k}.raw`),Buffer.from(bytes));invalid.push({job:job.index,stride});
  }
 }
 fs.writeFileSync(path.join(out,'execution.json'),JSON.stringify({rows,invalid,imports:0,node:process.version,v8:process.versions.v8}));
})().catch(error=>{console.error(error);process.exitCode=1;});
