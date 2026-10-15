'use strict';
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto'),assert=require('assert/strict');
const dir='/private/tmp/guard-identity-integration';
const {runObserved}=require(dir+'/observed_compiler.js');
const python='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9';
const helper='/Users/8amps/xcpreviewer-rs/research/build/libproc-observer/owned-process-snapshot';
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'guard-integration-'));fs.chmodSync(root,0o700);
 const fake=path.join(root,'missing-observer');fs.writeFileSync(fake,'#!'+python+'\nprint("[]")\n',{mode:0o700});
 const results=[];
 for(const spec of [{name:'real-owned-exit',helper,cap:65536},{name:'injected-live-omission',helper:fake,cap:65536},{name:'diagnostic-output-cap',helper:fake,cap:32}]){
  let record=null,error=null;const observations=[];
  try{record=await runObserved(python,['-S','-c','import time; time.sleep(0.2)'],{observer:{helper:spec.helper,sha256:hash(spec.helper)},supervisorPython:python,timeout:1500,limit:spec.cap,onObservation:v=>{observations.push(...v);}});}catch(e){record=e.record||null;error=String(e);}
  results.push({name:spec.name,cap:spec.cap,error,record,observations});
 }
 const [ok,missing,capped]=results;
 const checks={real_owned_exit:!ok.error&&ok.record?.report?.target_code===0&&ok.record?.report?.drained===true,
  omission_rejected:Boolean(missing.error)&&missing.record?.report?.drained===false,
  diagnostic_captured:missing.record?.stderr.includes('missing_live_target_identity')===true,
  output_cap_rejected:Boolean(capped.error)&&capped.record?.privateAbortRequested===true&&capped.record?.stderrBytes<=32};
 const output={scope:'Actual JS/Python pipes and owned child lifetime; injected missing observer is not native libproc failure evidence. Fault groups killed as fallback, cleanup unverified.',root,source_pins:{js:hash(dir+'/observed_compiler.js'),anchor:hash(dir+'/observed_group_anchor.py'),native_helper:hash(helper)},results,checks};
 fs.writeFileSync(dir+'/result.json',JSON.stringify(output,null,2)+'\n',{mode:0o600});
 console.log(JSON.stringify({checks,results:results.map(v=>({name:v.name,error:v.error,report:v.record?.report,privateAbortRequested:v.record?.privateAbortRequested}))}));
 if(!Object.values(checks).every(Boolean))process.exitCode=1;
})();
