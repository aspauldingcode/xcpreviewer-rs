'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {runObserved}=require('../reloop/observed_compiler.js'),{SourceRevisionHost}=require('../reloop/source_revision_host.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const source=fs.readFileSync(cfg.source),expected=fs.readFileSync(cfg.expected),initial=fs.readFileSync(cfg.module),config=cfg.config;
const args=(file,module)=>['--edition=2021','--target','wasm32-wasip1','--crate-type','cdylib','-C','panic=abort','-C','opt-level=2','-C','link-arg=--initial-memory=131072','-C','link-arg=--max-memory=131072','-C','link-arg=-zstack-size=8192',file,'-o',module];
(async()=>{
 assert.equal(sha(fs.readFileSync(cfg.linker)),cfg.linkerSha);const host=new SourceRevisionHost(),ticket=host.begin(source),base=await host.submit(ticket,{sourceSha256:sha(source),moduleSha256:sha(initial),module:initial,config,stride:64},expected),controls=[];fs.writeFileSync(path.join(out,'baseline.raw'),base.frame);
 try{
  let text=fs.readFileSync(cfg.generated,'utf8');for(let i=0;i<6000;i++)text+='\n#[no_mangle] pub extern "C" fn stress_'+i+'()->u32 {'+i+'}\n';
  for(const mode of ['abort','complete']){
   const file=path.join(out,mode+'.rs'),target=path.join(out,mode+'.wasm');fs.writeFileSync(file,text);const abort=new AbortController();let observed=null,execution,error=null;
   try{execution=await runObserved(cfg.rustc,args(file,target),{observer:cfg.observer,supervisorPython:cfg.python,timeout:5000,signal:abort.signal,onObservation:rows=>{
    const linker=rows.find(r=>r.identity[2]===cfg.linker&&r.state==='L');if(linker&&!observed){observed=linker;if(mode==='abort')abort.abort();}
   }});}catch(e){error=e;execution=e.record;}
   fs.writeFileSync(path.join(out,mode+'-attempt.json'),JSON.stringify({mode,observed,execution,error:error?String(error):null},null,2)+'\n');
   assert(observed,'Actual live pinned rust-lld identity must be observed');assert(execution&&execution.report.drained&&execution.report.remaining_observed===0);assert.equal(execution.emergencyClosed,false);
   if(mode==='abort'){assert(error);assert.equal(execution.report.failure,'abort');assert(Number.isInteger(execution.report.target_code));assert(execution.privateAbortRequested);}
   else{
    assert.equal(error,null);assert.equal(execution.report.target_code,0);assert.equal(execution.report.failure,null);const bytes=fs.readFileSync(target),m=new WebAssembly.Module(bytes);assert.equal(WebAssembly.Module.imports(m).length,0);assert.equal(WebAssembly.Module.exports(m).length,6004);const e=new WebAssembly.Instance(m).exports;assert.equal(e.capacity(),16384);assert.equal(e.render(64),config.height*64);const actual=Buffer.from(new Uint8Array(e.memory.buffer,e.pixels(),16384));assert(actual.equals(expected));fs.writeFileSync(path.join(out,'complete.raw'),actual);
   }
   assert.deepEqual(host.snapshot(),base);assert.deepEqual(await host.verifyLive(),base);fs.writeFileSync(path.join(out,mode+'-retained.raw'),base.frame);
   const before=fs.existsSync(target)?sha(fs.readFileSync(target)):null;await new Promise(r=>setTimeout(r,250));const after=fs.existsSync(target)?sha(fs.readFileSync(target)):null;assert.equal(after,before);
   controls.push({mode,observed,outcome:mode==='complete'?'completed':execution.report.target_code===0?'completed-before-abort-drain':'nonzero-after-abort',execution,error:error?String(error):null,lateArtifactStable:true,artifactPresent:before!==null,artifactSha:before,retainedRevision:1,retainedSha:sha(base.frame)});
  }
  const reuse=await host.submit(host.begin(source),{sourceSha256:sha(source),moduleSha256:sha(initial),module:initial,config,stride:64},expected);assert.equal(reuse.revision,2);assert(reuse.frame.equals(expected));fs.writeFileSync(path.join(out,'reuse.raw'),reuse.frame);await host.close();assert.equal(host.status().liveWorkers,0);assert.equal(sha(fs.readFileSync(cfg.linker)),cfg.linkerSha);
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,reuseRevision:2,status:host.status(),scope:'Actual linker live observation precedes cancellation request; completion may win abort drain; stress completion and baseline module reuse; not kernel reclamation or native Canvas transport'},null,2)+'\n');
 }finally{await host.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
