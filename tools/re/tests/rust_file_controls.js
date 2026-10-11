'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {SourceFileLoop}=require('../reloop/source_file_loop.js'),{rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const sources=[0,1,2].map(n=>fs.readFileSync(path.join(cfg.input,n+'-source.swift'))),expected=[0,1,2].map(n=>fs.readFileSync(path.join(cfg.input,n+'-expected.raw'))),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const results={scope:'Actual finite Rust source builder and owned file-loop generation/close boundaries; not linker-phase cancellation, kernel reclamation or native Canvas protocol'};
 for(const mode of ['stale','close']){
  const root=path.join(out,mode);fs.mkdirSync(root);const file=path.join(root,'owned.swift');let loop,armed=false,observed=null,closing=null,atClose=null;
  const write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
  const builder=rustSourceBuilder({...cfg,root,oracle:b=>{const n=sources.findIndex(s=>s.equals(b));assert(n>=0);return expected[n];},onObservation:rows=>{
   const compiler=rows.find(r=>r.identity[2]===cfg.rustc);
   if(armed&&compiler&&!observed){observed=compiler;if(mode==='stale'){write(sources[2]);void loop.poll();}else {atClose=loop.snapshot();closing=loop.close();}}
  }});
  loop=new SourceFileLoop(file,builder);
  try{
   write(sources[0]);await loop.start(250,10000);const base=loop.snapshot();assert.equal(base.revision,1);assert.deepEqual(base.frame,expected[0]);fs.writeFileSync(path.join(root,'baseline.raw'),base.frame);
   armed=true;write(sources[1]);await loop.poll();assert(observed,'Actual compiler process identity required');
   if(mode==='stale'){
    const final=loop.snapshot();assert.equal(final.revision,2);assert.deepEqual(final.frame,expected[2]);assert.deepEqual(await loop.verifyLive(),final);
    assert(loop.events().some(e=>e.kind==='rejected'&&/Stale or foreign/.test(e.error)));assert.equal(loop.events().filter(e=>e.kind==='published').length,2);
    assert.equal(builder.records().length,3);assert.equal(builder.failures().length,0);fs.writeFileSync(path.join(root,'final.raw'),final.frame);
    results.stale={observed,rejected:true,retainedRevision:1,finalRevision:2,finalSha:sha(final.frame)};
   }else{
    await closing;assert.equal(loop.snapshot(),null);assert(atClose);assert.equal(atClose.revision,base.revision);assert(atClose.frame.equals(base.frame));assert.equal(builder.records().length,1);assert.equal(builder.failures().length,1);
    const failure=builder.failures()[0].record;assert(failure.report.drained&&failure.report.remaining_observed===0);assert.equal(failure.report.failure,'abort');assert.notEqual(failure.report.target_code,0);assert.equal(failure.emergencyClosed,false);
    fs.writeFileSync(path.join(root,'final.raw'),atClose.frame);results.close={observed,closedSnapshotEmpty:loop.snapshot()===null,drained:true,retainedRevision:1,finalRevision:1,finalSha:sha(base.frame)};
   }
  }finally{await loop.close();}
  const artifacts=()=>fs.readdirSync(root).filter(n=>n.startsWith('build-')).map(n=>{const p=path.join(root,n,'result/view.wasm');return {stage:n,present:fs.existsSync(p),sha:fs.existsSync(p)?sha(fs.readFileSync(p)):null};});
  const before=artifacts();await new Promise(r=>setTimeout(r,250));assert.deepEqual(artifacts(),before);
  results[mode]={...results[mode],lateArtifactsStable:true,artifacts:before,events:loop.events(),builds:builder.records(),failures:builder.failures(),status:loop.status()};
  assert.equal(loop.status().liveWorkers,0);assert.equal(loop.status().timers,0);assert.equal(loop.status().building,false);
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(results,null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
