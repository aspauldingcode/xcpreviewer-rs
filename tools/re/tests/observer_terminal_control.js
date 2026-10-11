"use strict";
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {runObserved}=require(process.argv[3]);
const out=process.argv[2],python=process.argv[4];fs.mkdirSync(out,{recursive:true});
(async()=>{
 const controls=[];
 for(const mode of ['valid','trailing-partial','missing-accounting','negative-count','boolean-count']){
  const dir=path.join(out,mode);fs.mkdirSync(dir);const helper=path.resolve(dir,'unused-owned-helper'),supervisor=path.resolve(dir,'owned-supervisor');
  fs.writeFileSync(helper,'unused owned helper');const sha256=crypto.createHash('sha256').update(fs.readFileSync(helper)).digest('hex');
  const row={kind:'complete',target_code:0,failure:null,drained:true,tracked:1,observations:1,remaining_observed:0,scope:'Owned control fixture; no target launched'};
  if(mode==='missing-accounting'){delete row.tracked;delete row.observations;}
  if(mode==='negative-count')row.tracked=-1;
  if(mode==='boolean-count')row.observations=true;
  const payload=JSON.stringify(row)+'\n'+(mode==='trailing-partial'?'unterminated-private-data':'');
  fs.writeFileSync(supervisor,`#!${python}\nimport os,time\nos.write(3,${JSON.stringify(payload)}.encode())\nwhile True:time.sleep(3600)\n`,{mode:0o700});
  let record,error=null;const start=performance.now();
  try{record=await runObserved(python,['-c','raise Exception("not executed")'],{observer:{helper,sha256},supervisorPython:supervisor,timeout:50});}
  catch(e){error=String(e);record=e.record;}
  assert(record);controls.push({mode,record,error,elapsedMs:performance.now()-start});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,scope:'Owned supervisor protocol fixtures; no target launched'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
