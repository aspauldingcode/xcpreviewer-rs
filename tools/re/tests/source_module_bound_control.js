
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {SourceRevisionHost}=require(process.argv[2]);
const fixture=path.resolve(process.argv[3]),out=process.argv[4];
const row=JSON.parse(fs.readFileSync(path.join(fixture,'fixtures.json')))[0];
const read=name=>fs.readFileSync(path.join(fixture,'0-'+name));
(async()=>{
 const h=new SourceRevisionHost();let receiptReads=0,error;
 try{
  const baseline=await h.submit(h.begin(read('source.swift')),{module:read('view.wasm'),moduleSha256:row.module_sha256,sourceSha256:row.source_sha256,config:row.config,stride:row.stride},read('expected.raw'));
  const candidate={sourceSha256:row.source_sha256,module:Buffer.alloc(1048577),get moduleSha256(){++receiptReads;throw Error('late receipt read');}};
  try{await h.submit(h.begin(read('source.swift')),candidate,read('expected.raw'));}catch(e){error=String(e);}
  assert.deepEqual(h.snapshot(),baseline);assert.deepEqual(await h.verifyLive(),baseline);
  const result={module_bytes:1048577,limit_bytes:1048576,receipt_reads:receiptReads,error,retained_baseline:true,full_frame_bytes_verified:baseline.frame.length,passed:receiptReads===0&&error.includes('Module exceeds 1 MiB limit')};
  await h.close();result.final_owned_workers=h.status().liveWorkers;assert.equal(result.final_owned_workers,0);
  fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
  if(process.argv[5]!=='observe')assert(result.passed);
 }finally{await h.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
