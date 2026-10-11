'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {runOwned}=require(process.argv[3] || '../reloop/owned_compiler.js');
const out=process.argv[2],python=process.argv[4],observe=process.argv[5]==='observe';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const controls=[];
 for(const exit of [0,7]){
  const late=path.join(out,'late-'+exit),code='import os,time,sys\npid=os.fork()\nif pid==0:\n time.sleep(0.8)\n open(sys.argv[1],"w").write("late")\nelse:\n print("owned-child-started",flush=True)\n os._exit(int(sys.argv[2]))\n';
  const start=performance.now();let result,error;
  try{result=await runOwned(python,['-c',code,late,String(exit)],{timeout:process.argv[5]==='unit'?1000:200,supervisorPython:python});}catch(e){error=e;result=e.record;}
  const elapsed=performance.now()-start;await new Promise(r=>setTimeout(r,900));
  assert.match(result.stdout,/owned-child-started/);
  const passed=!fs.existsSync(late)&&elapsed<(process.argv[5]==='unit'?1500:700)&&(exit===0?!error:!!error&&result.code===7);
  controls.push({targetExit:exit,elapsedMs:elapsed,code:result.code,signal:result.signal,lateWriteAbsent:!fs.existsSync(late),error:error?String(error):null,passed});
  if(!observe)assert(passed,'Owned root-exit orphan cleanup failed');
 }
 fs.writeFileSync(path.join(out,'orphan-result.json'),JSON.stringify({controls,failures:controls.filter(c=>!c.passed).length,scope:'Known inherited group held by private supervisor anchor; no escaping descendants or native Canvas policy'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
