const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const [modulePath,out,mode]=process.argv.slice(2),module=await WebAssembly.compile(fs.readFileSync(modulePath));
 const imports=WebAssembly.Module.imports(module);assert.equal(imports.length,0);
 if(mode==='checker'){
  const e=(await WebAssembly.instantiate(module,{})).exports,rows=[];
  for(let variant=0;variant<40;variant++) for(let mutation=0;mutation<5;mutation++){
   const count=e.verify(variant,mutation);assert.equal(count,mutation?1:0);rows.push({variant,mutation,count});
  }
  for(let mutation=0;mutation<5;mutation++)assert.equal(e.verify_all(mutation),mutation?40:0);
  assert.equal(e.verify(40,0)>>>0,0xffffffff);assert.equal(e.verify(0,5)>>>0,0xffffffff);
  fs.writeFileSync(path.join(out,'checker-v8.json'),JSON.stringify({rows,imports}));return;
 }
 const cases=JSON.parse(fs.readFileSync(path.join(out,'inputs.json'))),rows=[],invalid=[];
 for(let variant=0;variant<cases.length;variant++) for(let reverse=0;reverse<2;reverse++) for(const [w,h,stride] of [[17,9,80],[1,1,8],[64,64,256],[31,7,132]])for(let repeat=0;repeat<2;repeat++){
  const e=(await WebAssembly.instantiate(module,{})).exports;assert.equal(e.capacity(),16384);
  const bytes=new Uint8Array(e.memory.buffer,e.pixels(),e.capacity());bytes.fill(0xc3);
  assert.equal(e.render(w,h,stride,...cases[variant],reverse),stride*h);
  const index=rows.length;fs.writeFileSync(path.join(out,`frame-${index}.raw`),Buffer.from(bytes));rows.push({index,variant,reverse,w,h,stride,repeat});
 }
 const e=(await WebAssembly.instantiate(module,{})).exports,bytes=new Uint8Array(e.memory.buffer,e.pixels(),e.capacity());bytes.fill(0xc3);
 assert.equal(e.render(17,9,80,4,2,8,0),720);const before=Buffer.from(bytes);fs.writeFileSync(path.join(out,'invalid-before.raw'),before);
 const bad=[[0,9,80,4,2,8,0],[65,9,256,4,2,8,0],[17,0,80,4,2,8,0],[17,65,80,4,2,8,0],[17,9,67,4,2,8,0],[17,9,257,4,2,8,0],[17,9,80,9,2,8,0],[17,9,80,4,9,8,0],[17,9,80,4,2,9,0],[17,9,80,4,2,8,2]];
 for(let i=0;i<7;i++){const args=[17,9,80,4,2,8,0];args[i]=0xffffffff;bad.push(args);}
 for(const [index,args] of bad.entries()){
  assert.equal(e.render(...args),0);assert.deepEqual(Buffer.from(bytes),before);fs.writeFileSync(path.join(out,`invalid-${index}.raw`),Buffer.from(bytes));invalid.push(args);
 }
 fs.writeFileSync(path.join(out,'execution.json'),JSON.stringify({rows,invalid,imports,node:process.version,v8:process.versions.v8}));
})().catch(error=>{console.error(error);process.exitCode=1;});
