'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {runObserved}=require('../reloop/observed_compiler.js'),{SourceRevisionHost}=require('../reloop/source_revision_host.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const crypto=require('node:crypto'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const source=fs.readFileSync(cfg.source),expected=fs.readFileSync(cfg.expected),initial=fs.readFileSync(cfg.module),config=cfg.config;
const args=(file,module)=>['--edition=2021','--target','wasm32-wasip1','--crate-type','cdylib','-C','panic=abort','-C','opt-level=2','-C','link-arg=--initial-memory=131072','-C','link-arg=--max-memory=131072','-C','link-arg=-zstack-size=8192',file,'-o',module];
const options={observer:cfg.observer,supervisorPython:cfg.python};
(async()=>{
 const host=new SourceRevisionHost(),baseTicket=host.begin(source);const base=await host.submit(baseTicket,{sourceSha256:sha(source),moduleSha256:sha(initial),module:initial,config,stride:64},expected);
 fs.writeFileSync(path.join(out,'baseline.raw'),base.frame);const controls=[];
 try{
  for(const mode of ['abort','deadline','stale']){
   const file=path.join(out,mode+'.rs'),module=path.join(out,mode+'.wasm'),ticket=host.begin(source),abort=new AbortController();let observed=null,execution,error=null;
   let text=fs.readFileSync(cfg.generated,'utf8');if(mode!=='stale')for(let i=0;i<6000;i++)text+='\n#[no_mangle] pub extern "C" fn stress_'+i+'()->u32 {'+i+'}\n';fs.writeFileSync(file,text);
   try{execution=await runObserved(cfg.rustc,args(file,module),{...options,signal:abort.signal,timeout:mode==='deadline'?300:5000,onObservation:rows=>{
    const target=rows.find(r=>r.identity[2]===cfg.rustc);if(target&&!observed){observed=target;if(mode==='abort')abort.abort();if(mode==='stale')host.begin(Buffer.from(source.toString()+' '));}
   }});if(mode==='stale'){const bytes=fs.readFileSync(module);await host.submit(ticket,{sourceSha256:sha(source),moduleSha256:sha(bytes),module:bytes,config,stride:64},expected);}}
   catch(e){error=e;execution=e.record||execution;}
   assert(observed,'Actual compiler identity must be observed');assert(error&&execution);assert(execution.report.drained&&execution.report.remaining_observed===0);assert.equal(execution.emergencyClosed,false);
   if(mode==='stale'){assert.match(String(error),/Stale or foreign/);assert.equal(execution.report.target_code,0);assert.equal(execution.report.failure,null);}
   else{assert.equal(execution.report.failure,mode==='abort'?'abort':'deadline');assert(execution.report.target_code!==0);}
   assert.deepEqual(host.snapshot(),base);assert.deepEqual(await host.verifyLive(),base);
   const before=fs.existsSync(module)?fs.readFileSync(module):null;await new Promise(r=>setTimeout(r,350));const after=fs.existsSync(module)?fs.readFileSync(module):null;assert.deepEqual(after,before);
   fs.writeFileSync(path.join(out,mode+'-retained.raw'),host.snapshot().frame);
   controls.push({mode,observed,execution,error:String(error),retainedRevision:base.revision,retainedSha:sha(base.frame),lateArtifactStable:true,artifactPresent:before!==null,artifactSha:before===null?null:sha(before)});
  }
  const file=path.join(out,'recovery.rs'),module=path.join(out,'recovery.wasm');fs.copyFileSync(cfg.generated,file);
  const execution=await runObserved(cfg.rustc,args(file,module),{...options,timeout:5000});const bytes=fs.readFileSync(module),ticket=host.begin(source);
  const recovery=await host.submit(ticket,{sourceSha256:sha(source),moduleSha256:sha(bytes),module:bytes,config,stride:64},expected);assert.equal(recovery.revision,2);assert.deepEqual(recovery.frame,expected);assert.deepEqual(await host.verifyLive(),recovery);fs.writeFileSync(path.join(out,'recovery.raw'),recovery.frame);
  await host.close();assert.equal(host.status().liveWorkers,0);
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,recovery:{revision:2,moduleSha:sha(bytes),execution},finalStatus:host.status(),scope:'Actual owned Rust compiler workload cancellation/deadline and stale ticket; observed ancestry and late-file stability, not native Canvas release semantics'},null,2)+'\n');
 }finally{await host.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
