'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {runObserved}=require(process.argv[3]||'../reloop/observed_compiler.js');
const out=process.argv[2],python=process.argv[4],observer={helper:process.argv[5],sha256:process.argv[6]};fs.mkdirSync(out,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const controls=[];
 for(const mode of ['success','failure','timeout','abort']){
  const dir=path.join(out,mode);fs.mkdirSync(dir);const release=path.join(dir,'release'),late=path.join(dir,'late'),a=new AbortController();
  const code='import os,time,sys\nchild=os.fork()\nif child==0:\n os.setsid()\n deadline=time.monotonic()+1\n while not os.path.exists(sys.argv[1]) and time.monotonic()<deadline:time.sleep(.01)\n time.sleep(1.2)\n open(sys.argv[2],"w").write("late")\n os._exit(0)\ndeadline=time.monotonic()+4\nwhile not os.path.exists(sys.argv[1]) and time.monotonic()<deadline:time.sleep(.01)\nos._exit(int(sys.argv[3]))\n';
  let observed=null,record,error=null;
  try{record=await runObserved(python,['-c',code,release,late,mode==='failure'?'7':'0'],{observer,supervisorPython:python,signal:a.signal,timeout:mode==='timeout'?500:3000,onObservation:rows=>{
   const child=rows.find(r=>r.group===r.pid);if(child&&!observed){observed=child;if(mode==='success'||mode==='failure')fs.writeFileSync(release,'release');if(mode==='abort')a.abort();}
  }});}catch(e){error=e;record=e.record;}
  assert(observed);assert.equal(record.report.drained,true);assert.equal(record.report.remaining_observed,0);assert(record.report.tracked>=2);
  assert.equal(record.signal,'SIGKILL');assert.equal(record.report.failure,mode==='timeout'?'deadline':mode==='abort'?'abort':null);
  if(mode==='success')assert(!error);else assert(error);
  if(mode==='success'||mode==='failure')assert.equal(record.report.target_code,mode==='success'?0:7);
  await sleep(2400);assert(!fs.existsSync(late));
  controls.push({mode,observed,record,error:error?String(error):null,lateWriteAbsent:true});
 }
 const before=new AbortController();before.abort();let preabort=false;try{await runObserved(python,['-c','raise Exception()'],{observer,signal:before.signal});}catch(e){preabort=/before spawn/.test(String(e));}assert(preabort);
 const stdinControl=await runObserved(python,['-c','import os; assert os.read(0,1)==b""; print("stdin-closed")'],{observer,supervisorPython:python,timeout:1000});assert.equal(stdinControl.stdout,'stdin-closed\n');
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,preabort,stdinControl,scope:'Explicit sampled full-identity public observer plus inherited group; unseen escapes and native Canvas release policy excluded'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
