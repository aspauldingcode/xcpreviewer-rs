const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
(async()=>{
 const [modulePath,out,mode]=process.argv.slice(2);
 const module=await WebAssembly.compile(fs.readFileSync(modulePath));
 const imports=WebAssembly.Module.imports(module);assert.equal(imports.length,0);
 if(mode==='checker'){
  const {verify}=(await WebAssembly.instantiate(module,{})).exports;
  const rows=[];
  for(let variant=0;variant<8;variant++) for(let mutation=0;mutation<4;mutation++){
   const mismatches=verify(variant,mutation);assert.equal(mismatches,mutation?1:0);
   rows.push({variant,mutation,mismatches});
  }
  fs.writeFileSync(path.join(out,'checker-v8.json'),JSON.stringify({rows,imports}));return;
 }
 const rows=[],invalid=[];
 const negatives=[[0,9,80,4,1],[65,9,256,4,1],[17,0,80,4,1],[17,65,80,4,1],[17,9,67,4,1],[17,9,257,4,1],[17,9,80,9,1],[17,9,80,4,2],[0xffffffff,9,80,4,1],[17,0xffffffff,80,4,1],[17,9,0xffffffff,4,1],[17,9,80,0xffffffff,1]];
 for(let n=0;n<=8;n++) for(let bg=0;bg<=1;bg++) for(const [w,h,stride] of [[17,9,68],[17,9,80],[3,2,15]]) for(let repeat=0;repeat<2;repeat++){
  const e=(await WebAssembly.instantiate(module,{})).exports;
  assert.equal(e.capacity(),16384);
  const bytes=new Uint8Array(e.memory.buffer,e.pixels(),e.capacity());bytes.fill(0xa5);
  assert.equal(e.render(w,h,stride,n,bg),stride*h);
  const index=rows.length;fs.writeFileSync(path.join(out,`frame-${index}.rgba`),Buffer.from(bytes));
  rows.push({index,w,h,stride,n,bg,repeat});
 }
 const e=(await WebAssembly.instantiate(module,{})).exports;
 const bytes=new Uint8Array(e.memory.buffer,e.pixels(),e.capacity());bytes.fill(0xa5);
 assert.equal(e.render(17,9,80,4,1),720);
 const before=Buffer.from(bytes);fs.writeFileSync(path.join(out,'invalid-before.rgba'),before);
 for(const [index,args] of negatives.entries()){
  assert.equal(e.render(...args),0);assert.deepEqual(Buffer.from(bytes),before);
  fs.writeFileSync(path.join(out,`invalid-${index}.rgba`),Buffer.from(bytes));invalid.push(args);
 }
 fs.writeFileSync(path.join(out,'execution.json'),JSON.stringify({rows,invalid,imports,node:process.version,v8:process.versions.v8}));
})().catch(error=>{console.error(error);process.exitCode=1;});
