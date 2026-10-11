'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {runObserved}=require(process.argv[3]||'../reloop/observed_compiler.js');
const out=process.argv[2],python=process.argv[4],helper=process.argv[5],sha256=process.argv[6];fs.mkdirSync(out,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const controls=[];
 for(const mode of ['observer-loss-held-stdio','output-pressure']){
  const dir=path.join(out,mode);fs.mkdirSync(dir);const ownedHelper=path.join(dir,'owned-helper'),release=path.join(dir,'release'),late=path.join(dir,'late');fs.copyFileSync(helper,ownedHelper);fs.chmodSync(ownedHelper,0o700);
  const code='import os,time,sys\nif os.fork()==0:\n os.setsid()\n time.sleep(float(sys.argv[3]))\n open(sys.argv[2],"w").write("late")\n os._exit(0)\ndeadline=time.monotonic()+8\nwhile not os.path.exists(sys.argv[1]) and time.monotonic()<deadline:time.sleep(.01)\nprint("x"*80000,flush=True)\ntime.sleep(8)\n';
  let observed=null,record,error=null;const start=performance.now();
  try{record=await runObserved(python,['-c',code,release,late,mode==='output-pressure'?'1.2':'7'],{observer:{helper:path.resolve(ownedHelper),sha256},supervisorPython:python,timeout:mode==='output-pressure'?3000:500,limit:1024,onObservation:rows=>{
   const child=rows.find(r=>r.group===r.pid);if(child&&!observed){observed=child;if(mode==='output-pressure')fs.writeFileSync(release,'release');else fs.writeFileSync(ownedHelper,'owned observer deliberately unavailable');}
  }});}catch(e){error=e;record=e.record;}
  const elapsed=performance.now()-start;assert(observed&&error&&record);assert(record.stdout.length+record.stderr.length<=1024);
  if(mode==='output-pressure'){
   assert.match(String(error),/output limit/);assert.equal(record.report.drained,true);assert.equal(record.report.failure,'abort');assert.equal(record.report.remaining_observed,0);assert.equal(record.emergencyClosed,false);assert(elapsed<2000);
   await sleep(1500);assert(!fs.existsSync(late));
  }else{
   assert.equal(record.report.drained,false);assert.match(record.report.failure,/AssertionError/);assert.equal(record.emergencyClosed,true);assert(elapsed>=5000&&elapsed<6500);
   // The child owns stdout after supervisor retirement. Unknown cleanup must
   // reject, even though owned pipe closure bounded the caller's settlement.
   await sleep(2200);assert.equal(fs.readFileSync(late,'utf8'),'late');
  }
  controls.push({mode,observed,record,error:String(error),elapsedMs:elapsed,lateWritePresent:fs.existsSync(late)});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,scope:'Observed owned helper loss and output pressure; forced pipe closure is not descendant release or native Canvas evidence'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
