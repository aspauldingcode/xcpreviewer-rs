"use strict";
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {runObserved}=require(process.argv[3]);
const out=process.argv[2],python=process.argv[4],observer={helper:process.argv[5],sha256:process.argv[6]};fs.mkdirSync(out,{recursive:true});
(async()=>{
 const release=path.join(out,'release'),late=path.join(out,'late'),a=new AbortController();let original=null,reparented=null,error=null,record;
 const code='import os,time,sys\nif os.fork()==0:\n os.setsid()\n time.sleep(1.8)\n open(sys.argv[2],"w").write("late")\n os._exit(0)\ndeadline=time.monotonic()+2\nwhile not os.path.exists(sys.argv[1]) and time.monotonic()<deadline:time.sleep(.005)\nos._exit(0)\n';
 try{record=await runObserved(python,['-c',code,release,late],{observer,supervisorPython:python,timeout:2500,signal:a.signal,onObservation:rows=>{
  for(const row of rows){if(row.group!==row.pid)continue;
   if(!original){original=row;fs.writeFileSync(release,'release');}
   else if(row.pid===original.pid&&row.parent!==original.parent){reparented=row;a.abort();}
  }
 }});}catch(e){error=String(e);record=e.record;}
 fs.writeFileSync(path.join(out,"diagnostic.json"),JSON.stringify({original,reparented,error,record},null,2));
 assert(original&&reparented);assert.deepEqual(reparented.identity,original.identity);assert(error&&/aborted/.test(error));
 assert.equal(record.privateAbortRequested,true);assert.equal(record.report.target_code,0);assert.equal(record.report.drained,true);assert.equal(record.report.remaining_observed,0);assert.equal(record.emergencyClosed,false);
 await new Promise(r=>setTimeout(r,2000));assert(!fs.existsSync(late));
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({original,reparented,error,record,lateWriteAbsent:true,scope:'Abort at observed owned reparenting after actual parent exit; not native Canvas semantics'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
