'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {LiveWasmHost}=require('./live_wasm_host.js');
const input=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const index=JSON.parse(fs.readFileSync(path.join(input,'corpus.json')));
function read(name,suffix){
 assert(new RegExp('^[0-9a-f]{64}\\'+suffix+'$').test(name),'Content-addressed fixture required');
 const file=path.join(input,name);assert(!fs.lstatSync(file).isSymbolicLink());
 const bytes=fs.readFileSync(file);assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),name.slice(0,64));return bytes;
}
(async()=>{
 assert.equal(index.version,1);assert.equal(index.records.length,84);
 fs.mkdirSync(out,{recursive:true});const host=new LiveWasmHost(),records=[],faults=[];
 let previous;
 try{
  for(const [n,row] of index.records.entries()){
   const module=read(row.module,'.wasm'),expected=read(row.expected,'.raw'),native=row.native?read(row.native,'.raw'):null;
   assert.equal(expected.length,16384);if(native)assert.deepEqual(native,expected,'Native/independent gate before publication');
   const frame=await host.propose(module,expected,row.config.width,row.config.height,row.stride);
   assert.equal(frame.revision,n+1);if(previous)assert.notEqual(frame.token,previous.token);
   assert.deepEqual(frame.frame,expected);if(native)assert.deepEqual(frame.frame,native);
   assert.deepEqual(await host.verifyLive(),frame);assert.equal(host.status().liveWorkers,1);
   fs.writeFileSync(path.join(out,'revision-'+n+'.raw'),frame.frame);
   records.push({job:row.job,repeat:row.repeat,revision:frame.revision,module_sha256:frame.moduleSha256,
     allocation_sha256:crypto.createHash('sha256').update(frame.frame).digest('hex'),native_bytes:native?16384:0,independent_bytes:16384,live_bytes:16384});
   if(n===6){
    assert.equal(row.config.width,13);assert.equal(row.stride,64);
    for(const [name,offset] of [['pixel',0],['padding',52],['tail',16383]]){
     const corrupt=Buffer.from(expected);corrupt[offset]^=1;let error;
     try{await host.propose(module,corrupt,row.config.width,row.config.height,row.stride);}catch(e){error=String(e);}
     assert(error);assert.deepEqual(host.snapshot(),frame);assert.deepEqual(await host.verifyLive(),frame);assert.equal(host.status().liveWorkers,1);
     faults.push({name,offset,error,retained_revision:frame.revision,compared_bytes:16384,live_bytes:16384});
    }
   }
   previous=frame;
  }
  await host.close();assert.equal(host.status().liveWorkers,0);
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({node:process.version,v8:process.versions.v8,platform:process.platform,architecture:process.arch,records,faults,final_status:host.status(),scope:index.scope},null,2)+'\n');
 }finally{await host.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
