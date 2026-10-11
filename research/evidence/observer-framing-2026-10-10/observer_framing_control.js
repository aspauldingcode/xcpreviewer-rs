"use strict";
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {runObserved}=require(process.argv[3]);
const out=process.argv[2],python=process.argv[4];fs.mkdirSync(out,{recursive:true});
(async()=>{
 const controls=[];
 for(const mode of ['split-utf8','invalid-utf8','ascii-bytewise']){
  const dir=path.join(out,mode);fs.mkdirSync(dir);const helper=path.resolve(dir,'unused-helper'),supervisor=path.resolve(dir,'owned-supervisor');fs.writeFileSync(helper,'unused owned helper');
  const sha256=crypto.createHash('sha256').update(fs.readFileSync(helper)).digest('hex');
  const scope=mode==='ascii-bytewise'?'owned-ascii':'owned-é';
  const row={kind:'complete',target_code:0,failure:null,drained:true,tracked:1,observations:1,remaining_observed:0,scope};
  const bytes=Buffer.from(JSON.stringify(row)+'\n');let parts;
  if(mode==='ascii-bytewise')parts=Array.from(bytes,b=>[b]);
  else{const start=bytes.indexOf(Buffer.from('é'));if(mode==='invalid-utf8'){bytes[start]=255;parts=[Array.from(bytes)];}else parts=[Array.from(bytes.subarray(0,start+1)),Array.from(bytes.subarray(start+1))];}
  // Explicit finite delay separates native pipe deliveries across the codepoint.
  const source=`#!${python}\nimport os,time\nfor part in ${JSON.stringify(parts)}:\n os.write(3,bytes(part))\n time.sleep(.01)\nwhile True:time.sleep(3600)\n`;
  fs.writeFileSync(supervisor,source,{mode:0o700});let error=null,record;const start=performance.now();
  try{record=await runObserved(python,['-c','raise Exception("not executed")'],{observer:{helper,sha256},supervisorPython:supervisor,timeout:2500});}catch(e){error=String(e);record=e.record;}
  assert(record);controls.push({mode,expectedScope:scope,record,error,elapsedMs:performance.now()-start});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,scope:'Explicit owned private-stream segmentation; no target launched'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
