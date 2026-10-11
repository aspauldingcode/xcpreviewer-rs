'use strict';
// Deterministic owned policy boundary after actual compilation and validation.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {SourceFileLoop}=require('../reloop/source_file_loop.js');
const {rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const sources=[0,1,2].map(n=>fs.readFileSync(path.join(cfg.input,n+'-source.swift'))),expected=[0,1,2].map(n=>fs.readFileSync(path.join(cfg.input,n+'-expected.raw')));
(async()=>{
 const result={scope:'Owned file-loop publication veto after successful actual Rust subprocess completion; not native cancellation timing or Canvas transport',controls:[]};
 for(const mode of ['close','supersede']){
  const root=path.join(out,mode);fs.mkdirSync(root);const file=path.join(root,'owned.swift');let loop,armed=false,boundary=null,closing=null;
  const write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
  const builder=rustSourceBuilder({...cfg,root,oracle:source=>{
   const n=sources.findIndex(s=>s.equals(source));assert(n>=0);
   if(armed&&n===1&&!boundary){
    boundary={phase:'oracle-after-successful-execution',revision:loop.snapshot().revision,frameMatchesBaseline:loop.snapshot().frame.equals(expected[0])};
    if(mode==='close')closing=loop.close();else{write(sources[2]);void loop.poll();}
   }
   return expected[n];
  }});
  loop=new SourceFileLoop(file,builder);
  try{
   write(sources[0]);await loop.start(250,10000);assert.equal(loop.snapshot().revision,1);assert.deepEqual(loop.snapshot().frame,expected[0]);fs.writeFileSync(path.join(root,'baseline.raw'),loop.snapshot().frame);
   armed=true;write(sources[1]);await loop.poll();assert(boundary&&boundary.frameMatchesBaseline);assert.equal(boundary.revision,1);
   if(mode==='close'){await closing;assert.equal(loop.snapshot(),null);assert.equal(builder.records().length,2);}
   else{assert.equal(loop.snapshot().revision,2);assert.deepEqual(loop.snapshot().frame,expected[2]);assert.deepEqual(await loop.verifyLive(),loop.snapshot());fs.writeFileSync(path.join(root,'final.raw'),loop.snapshot().frame);assert.equal(builder.records().length,3);}
   assert.equal(builder.failures().length,0);
   const rejected=loop.events().filter(e=>e.kind==='rejected');assert.equal(rejected.length,1);assert.equal(rejected[0].generation,2);
   assert.match(rejected[0].error,mode==='close'?/File loop closed before publication/:/Stale or foreign build ticket/);
   assert.deepEqual(loop.events().filter(e=>e.kind==='published').map(e=>e.generation),mode==='close'?[1]:[1,3]);
   for(const record of builder.records()){assert.equal(record.execution.report.target_code,0);assert.equal(record.execution.report.failure,null);assert.equal(record.execution.report.remaining_observed,0);assert(record.execution.report.drained);}
  }finally{await loop.close();}
  const status=loop.status();assert(status.loopClosed&&!status.building&&status.timers===0&&status.liveWorkers===0);
  result.controls.push({mode,boundary,closedSnapshotEmpty:loop.snapshot()===null,events:loop.events(),builds:builder.records(),failures:builder.failures(),status});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
