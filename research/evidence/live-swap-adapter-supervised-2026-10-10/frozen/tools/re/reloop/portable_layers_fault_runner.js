const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const [modulePath,output]=process.argv.slice(2),module=await WebAssembly.compile(fs.readFileSync(modulePath));
 const imports=WebAssembly.Module.imports(module);assert.equal(imports.length,0);
 const e=(await WebAssembly.instantiate(module,{})).exports,rows=[];
 for(let variant=0;variant<40;variant++)rows.push({variant,mismatches:e.verify(variant,0)>>>0});
 assert.equal(e.verify_all(0)>>>0,0xffffffff);assert.ok(rows.some(r=>r.mismatches>0 && r.mismatches!==0xffffffff));
 assert.ok(rows.slice(0,8).every(r=>r.mismatches===0));
 fs.writeFileSync(output,JSON.stringify({rows,imports,witness:e.verify(8,0)>>>0,node:process.version,v8:process.versions.v8}));
})().catch(error=>{console.error(error);process.exitCode=1;});
