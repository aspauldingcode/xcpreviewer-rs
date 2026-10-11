'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {runObserved}=require('../reloop/observed_compiler.js');const {SourceFileLoop}=require('../reloop/source_file_loop.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const sources=[0,1,2].map(i=>fs.readFileSync(path.join(cfg.input,i+'-source.swift'))),builds=[],failures=[];
const builder=async(source,{signal})=>{
 const stage=fs.mkdtempSync(path.join(out,'build-')),file=path.join(stage,'source.swift');fs.writeFileSync(file,source);
 let execution;try{execution=await runObserved(cfg.python,[cfg.cli,file,'--output',path.join(stage,'result'),'--rustc',cfg.rustc,'--rustc-sha256',cfg.rustcSha],{signal,timeout:5000,observer:cfg.observer,supervisorPython:cfg.python});}
 catch(e){failures.push({error:String(e),record:e.record});throw e;}
 const r=JSON.parse(execution.stdout),module=fs.readFileSync(path.join(stage,'result/view.wasm'));assert.equal(r.source_sha256,sha(source));assert.equal(r.module_sha256,sha(module));assert.equal(r.rustc_sha256,cfg.rustcSha);
 assert(execution.report.drained&&execution.report.remaining_observed===0&&execution.report.target_code===0);
 const n=sources.findIndex(b=>b.equals(source));assert(n>=0);const expected=fs.readFileSync(path.join(cfg.input,n+'-expected.raw'));
 builds.push({receipt:r,execution,stage:path.basename(stage)});
 return {build:{module,moduleSha256:r.module_sha256,sourceSha256:r.source_sha256,config:r.config,stride:64},expected};
};
(async()=>{
 const file=path.join(out,'owned.swift'),write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);},loop=new SourceFileLoop(file,builder),records=[];
 try{
  write(sources[0]);await loop.start(25,10000);
  for(let n=0;n<3;n++){
   if(n){write(sources[n]);await loop.poll();}
   const frame=loop.snapshot();assert(frame);assert.equal(frame.revision,n+1);assert.deepEqual(frame.frame,fs.readFileSync(path.join(cfg.input,n+'-expected.raw')));assert.deepEqual(await loop.verifyLive(),frame);
   fs.writeFileSync(path.join(out,n+'-frame.raw'),frame.frame);records.push({revision:frame.revision,sha256:sha(frame.frame),sourceSha:sha(sources[n]),moduleSha:frame.moduleSha256});
  }
  const old=loop.snapshot();write(Buffer.from('Text("unsupported")'));await loop.poll();assert.deepEqual(loop.snapshot(),old);assert.deepEqual(await loop.verifyLive(),old);assert.equal(failures.length,1);assert.equal(failures[0].record.report.target_code,2);assert(failures[0].record.report.drained);await loop.close();assert.equal(loop.status().liveWorkers,0);
 }finally{await loop.close();}
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({records,builds,failures,finalStatus:loop.status(),scope:'Finite source-to-Rust-WASM and owned observed process drain; compatible state reset, not native Canvas semantics'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
