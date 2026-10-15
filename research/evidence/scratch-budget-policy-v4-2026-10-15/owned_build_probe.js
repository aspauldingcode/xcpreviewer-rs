'use strict';
// Research-only probe. Reuses the previously qualified observed compiler guard.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {execFileSync}=require('node:child_process');
const crypto=require('node:crypto');
const repo='/Users/8amps/xcpreviewer-rs';
const {runObserved,validateComplete}=require(repo+'/tools/re/reloop/observed_compiler.js');
const python='/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9';
const reserve=4*1024*1024;
function sinkBuffers(record,summary,limit=reserve){
 const stdout=Buffer.from(record?.stdout||'','utf8'),stderr=Buffer.from(record?.stderr||'','utf8');
 const report=Buffer.from(JSON.stringify(summary,null,2)+'\n','utf8');
 if(report.length>65536)throw Error('Report reserve exceeded');
 // Include a conservative 64KiB file-allocation allowance for each sink file.
 if(stdout.length+stderr.length+report.length+3*65536>limit)throw Error('Encoded sink reserve exceeded');
 return {stdout,stderr,report};
}
function admissible(v){
 const names=['retained_logical','scratch_logical','allocated','files','directories'];
 return names.every(k=>Number.isSafeInteger(v[k])&&v[k]>=0)&&
  v.retained_logical+reserve<=512*1024**2&&v.allocated+reserve<=512*1024**2&&
  v.scratch_logical<=25*1024**3&&v.files+v.directories<=100000;
}
function accepted(record,measurement){
 try{validateComplete(record.report);}catch(_){return false;}
 return record.report.drained===true&&record.report.remaining_observed===0&&
  record.report.target_code===0&&record.report.failure===null&&
  record.emergencyClosed===false&&record.signal==='SIGKILL'&&admissible(measurement);
}
function measure(root,identity,live=false){
 const code='import json,sys,time;sys.path.insert(0,sys.argv[1]);from scratch_budget import measure;print(json.dumps(measure(sys.argv[2],identity=tuple(map(int,sys.argv[3:5])),deadline=time.monotonic()+1,max_entries=100000,live=sys.argv[5]=="live")))';
 const env={...process.env};delete env.PYTHONPATH;
 return JSON.parse(execFileSync(python,['-S','-c',code,__dirname,root,...identity.map(String),live?'live':'final'],
  {env,timeout:2000,maxBuffer:65536,encoding:'utf8'}));
}
async function main(){
 const parent=fs.mkdtempSync(path.join(os.tmpdir(),'xcpreviewer-build-v3-'));
 fs.chmodSync(parent,0o700);
 const root=path.join(parent,'scratch');fs.mkdirSync(root,{mode:0o700});
 const st=fs.lstatSync(root),identity=[st.dev,st.ino];
 const helper=repo+'/research/build/libproc-observer/owned-process-snapshot';
 const expected='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5';
 const anchor=repo+'/tools/re/reloop/observed_group_anchor.py';
 if(crypto.createHash('sha256').update(fs.readFileSync(anchor)).digest('hex')!=='48c73a15ac5720ec653271bc6ec523a090fb2bff4301f2308a9812faea4187b8')throw Error('Guard source changed');
 const argv=['xcodebuild','-quiet','-project',repo+'/research/build/preview-workspaces/preview-2b3aaa1663864b3fa200cd0eed456444/PreviewLab.xcodeproj',
  '-scheme','PreviewLab','-configuration','Debug','-sdk','macosx','-destination','platform=macOS,arch=arm64',
  '-destination-timeout','3','-derivedDataPath',path.join(root,'DerivedData'),'CODE_SIGNING_ALLOWED=NO','build'];
 const controller=new AbortController();let measurementError=null,timer=null,record=null,error=null;
 const samples=[];let final=null;
 // Both measurement failure and budget excess request the guard's private abort.
 const sample=()=>{try{const value=measure(root,identity,true);samples.push({...value,provisional:true});if(!admissible(value))throw Error('Scratch/retained cap exceeded');}
  catch(e){measurementError ||= String(e);controller.abort();}};
 sample();
 if(measurementError)throw Error(measurementError);
 try{
  timer=setInterval(sample,250);
  record=await runObserved('/usr/bin/xcrun',argv,{observer:{helper,sha256:expected},supervisorPython:python,
    signal:controller.signal,timeout:30000,limit:1048576});
 }catch(e){error=String(e);record=e.record||null;}
 finally{if(timer)clearInterval(timer);}
 try{final=measure(root,identity);}catch(e){measurementError ||= String(e);}
 const success=!error&&!measurementError&&record&&final&&accepted(record,final);
 // A separately owned sink avoids pathname writes to a rejected scratch root.
 // Guard output is decoded text: invalid raw UTF-8 can expand threefold.
 const summary={scope:'Owned CLI build with previously qualified observed guard; no Canvas or image acceptance',
  parent,root,identity,argv,success:Boolean(success),error,measurementError,samples,final,
  record:record?Object.fromEntries(Object.entries(record).filter(([k])=>k!=='stdout'&&k!=='stderr')):null};
 const sink=sinkBuffers(record,summary);
 fs.writeFileSync(path.join(parent,'stdout.txt'),sink.stdout,{flag:'wx',mode:0o600});
 fs.writeFileSync(path.join(parent,'stderr.txt'),sink.stderr,{flag:'wx',mode:0o600});
 fs.writeFileSync(path.join(parent,'report.json'),sink.report,{flag:'wx',mode:0o600});
 const allocation=['stdout.txt','stderr.txt','report.json'].reduce((n,name)=>n+fs.statSync(path.join(parent,name)).blocks*512,0);
 if(allocation>reserve)throw Error('Sink allocation exceeded reserve; report is not accepted');
 process.stdout.write(JSON.stringify({parent,success:summary.success,error,measurementError,final,report:summary.record?.report})+'\n');
 process.exitCode=success?0:1;
}
module.exports={accepted,admissible,measure,sinkBuffers};
if(require.main===module)main().catch(e=>{process.stderr.write(String(e)+'\n');process.exitCode=1;});
