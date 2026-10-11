'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {SourceFileLoop}=require('../reloop/source_file_loop.js'),{rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const sources=[0,1,2].map(n=>fs.readFileSync(path.join(cfg.input,n+'-source.swift'))),expectations=[0,1,2].map(n=>fs.readFileSync(path.join(cfg.input,n+'-expected.raw'))),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const controls=[];
 for(const mode of ['deadline','pin','oracle']){
  const root=path.join(out,mode);fs.mkdirSync(root);const file=path.join(root,'owned.swift'),observations=[];
  const oracle=b=>{const n=sources.findIndex(s=>s.equals(b));assert(n>=0);return expectations[n];};
  const normal=rustSourceBuilder({...cfg,root:path.join(root,'normal'),oracle});
  const failed=rustSourceBuilder({...cfg,root:path.join(root,'failure'),timeout:mode==='deadline'?50:5000,toolchainPin:mode==='pin'?'0'.repeat(64):cfg.toolchainPin,oracle:mode==='oracle'?()=>{throw Error('Owned independent oracle rejection');}:oracle,onObservation:rows=>observations.push(...rows)});
  let calls=0;const builder=(source,options)=>(++calls===2?failed:normal)(source,options),loop=new SourceFileLoop(file,builder);
  const write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
  try{
   write(sources[0]);await loop.start(250,10000);const base=loop.snapshot();assert.equal(base.revision,1);assert(base.frame.equals(expectations[0]));fs.writeFileSync(path.join(root,'baseline.raw'),base.frame);
   write(sources[1]);await loop.poll();const retained=loop.snapshot();assert(retained&&retained.revision===1&&retained.frame.equals(base.frame));assert.deepEqual(await loop.verifyLive(),base);fs.writeFileSync(path.join(root,'retained.raw'),retained.frame);
   assert.equal(failed.failures().length,1);const failure=failed.failures()[0],report=failure.record.report;assert(report.drained&&report.remaining_observed===0);assert.equal(failure.record.emergencyClosed,false);
   assert(observations.some(r=>r.parent===failure.record.pid),'Actual owned CLI process observation required');
   if(mode==='deadline'){assert.equal(report.failure,'deadline');assert.equal(report.target_code,-15);}
   else if(mode==='pin'){assert.equal(report.target_code,2);assert.match(failure.record.stderr,/Pinned Rust target\/linker identity changed/);}
   else {assert.equal(report.target_code,0);assert.equal(report.failure,null);assert.match(failure.error,/Owned independent oracle rejection/);}
   write(sources[2]);await loop.poll();const final=loop.snapshot();assert.equal(final.revision,2);assert(final.frame.equals(expectations[2]));assert.deepEqual(await loop.verifyLive(),final);fs.writeFileSync(path.join(root,'recovery.raw'),final.frame);await loop.close();
   const artifacts=()=>fs.readdirSync(path.join(root,'failure')).filter(n=>n.startsWith('build-')).map(n=>{const p=path.join(root,'failure',n,'result/view.wasm');return {stage:n,present:fs.existsSync(p),sha:fs.existsSync(p)?sha(fs.readFileSync(p)):null};});
   const before=artifacts();assert.equal(before.length,1);assert.equal(before[0].present,mode==='oracle');await new Promise(r=>setTimeout(r,250));assert.deepEqual(artifacts(),before);
   assert.equal(loop.status().liveWorkers,0);assert.equal(loop.status().timers,0);assert.equal(loop.status().building,false);
   controls.push({mode,failure,observations,builds:normal.records(),failedBuilds:failed.records(),artifacts:before,lateArtifactsStable:true,events:loop.events(),retainedRevision:1,retainedSha:sha(retained.frame),recoveryRevision:2,recoverySha:sha(final.frame),status:loop.status()});
  }finally{await loop.close();}
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,scope:'Actual finite source-file build failure/deadline/recovery and postcompile oracle rejection; deadline covers CLI work before compiler, not linker or native Canvas release'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
