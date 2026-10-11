'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {runObserved}=require('../reloop/observed_compiler.js');const {SourceFileLoop}=require('../reloop/source_file_loop.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const sources=[0,1,2].map(i=>fs.readFileSync(path.join(cfg.input,i+'-source.swift'))),builds=[],failures=[];
const {rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const builder=rustSourceBuilder({...cfg,root:out,oracle:source=>{const n=sources.findIndex(b=>b.equals(source));assert(n>=0);return fs.readFileSync(path.join(cfg.input,n+'-expected.raw'));}});
(async()=>{
 const file=path.join(out,'owned.swift'),write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);},loop=new SourceFileLoop(file,builder),records=[];
 try{
  write(sources[0]);await loop.start(25,10000);
  for(let n=0;n<3;n++){
   if(n){write(sources[n]);await loop.poll();}
   const frame=loop.snapshot();assert(frame);assert.equal(frame.revision,n+1);assert.deepEqual(frame.frame,fs.readFileSync(path.join(cfg.input,n+'-expected.raw')));assert.deepEqual(await loop.verifyLive(),frame);
   fs.writeFileSync(path.join(out,n+'-frame.raw'),frame.frame);records.push({revision:frame.revision,sha256:sha(frame.frame),sourceSha:sha(sources[n]),moduleSha:frame.moduleSha256});
  }
  const old=loop.snapshot();write(Buffer.from('Text("unsupported")'));await loop.poll();assert.deepEqual(loop.snapshot(),old);assert.deepEqual(await loop.verifyLive(),old);assert.equal(builder.failures().length,1);assert.equal(builder.failures()[0].record.report.target_code,2);assert(builder.failures()[0].record.report.drained);await loop.close();assert.equal(loop.status().liveWorkers,0);
 }finally{await loop.close();}
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({records,builds:builder.records(),failures:builder.failures(),finalStatus:loop.status(),scope:'Finite source-to-Rust-WASM and owned observed process drain; compatible state reset, not native Canvas semantics'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
