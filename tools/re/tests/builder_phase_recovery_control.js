// Actual pinned owned Rust CLI build cancellation; sampled cleanup scope only.
'use strict';
const {spawn}=require('node:child_process');const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {SourceFileLoop}=require('../reloop/source_file_loop.js'),{rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const e=path.resolve(process.argv[2]),input=path.resolve(process.argv[3]),cfg=JSON.parse(fs.readFileSync(path.join(e,'config.json'))),sources=[0,1,2].map(i=>fs.readFileSync(path.join(input,i+'-source.swift'))),file=path.join(e,'owned.swift');let loop,trigger=null,watcherDone=null,watcherRecord=null;
const write=source=>{fs.writeFileSync(file+'.tmp',source);fs.renameSync(file+'.tmp',file);};
const observations=[];
cfg.oracle=source=>{const i=sources.findIndex(s=>s.equals(source));assert(i===0||i===2);return fs.readFileSync(path.join(e,i+'-expected.raw'));};
cfg.onObservation=rows=>{
 observations.push(rows);
 if(watcherDone||trigger||!fs.readFileSync(file).equals(sources[1]))return;
 const compiler=rows.find(row=>row.identity[2]===cfg.rustc);if(!compiler)return;
 const stages=fs.readdirSync(cfg.root).filter(name=>name.startsWith('build-')).map(name=>path.join(cfg.root,name));
 const stage=stages.find(dir=>fs.existsSync(path.join(dir,'result/module.rs'))&&!fs.existsSync(path.join(dir,'result/view.wasm'))&&fs.readFileSync(path.join(dir,'source.swift')).equals(sources[1]));if(!stage)return;
 assert.deepEqual(loop.snapshot().frame,fs.readFileSync(path.join(e,'0-expected.raw')));fs.writeFileSync(path.join(e,'retained-at-cancel.raw'),loop.snapshot().frame);
 watcherDone=new Promise((resolve,reject)=>{const w=spawn(cfg.watcher,[String(compiler.pid),String(compiler.identity[0]),String(compiler.identity[1]),cfg.rustc],{stdio:['ignore','pipe','pipe']});let stdout='',stderr='',registered=false;const deadline=setTimeout(()=>w.kill('SIGKILL'),5000);w.stdout.on('data',chunk=>{stdout+=chunk;const line=stdout.split('\n')[0];if(registered||!stdout.includes('\n'))return;try{const row=JSON.parse(line);assert.deepEqual(row,{registered:true,pid:compiler.pid,seconds:compiler.identity[0],micros:compiler.identity[1]});assert(!fs.existsSync(path.join(stage,'result/view.wasm')));registered=true;trigger={compiler,stage:path.basename(stage),generatedBeforeCancel:true,moduleAbsentBeforeCancel:true,registration:row};write(sources[2]);void loop.poll();}catch(error){reject(error);}});w.stderr.on('data',chunk=>stderr+=chunk);w.on('error',reject);w.on('close',(code,signal)=>{clearTimeout(deadline);watcherRecord={code,signal,stdout,stderr};fs.writeFileSync(path.join(e,'compiler-kernel-wait.json'),JSON.stringify(watcherRecord,null,2)+'\n');try{assert.equal(code,0);assert.equal(stderr,'');const lines=stdout.trim().split('\n').map(JSON.parse);assert.equal(lines.length,2);assert.equal(lines[1].pid,compiler.pid);assert.equal(lines[1].raw_status,15);resolve();}catch(error){reject(error);}});});watcherDone.catch(()=>{});
};
const builder=rustSourceBuilder(cfg);write(sources[0]);loop=new SourceFileLoop(file,builder);
(async()=>{
 try{
  await loop.poll();assert(loop.snapshot(),'Baseline actual build must qualify before cancellation');fs.writeFileSync(path.join(e,'baseline.raw'),loop.snapshot().frame);
  write(sources[1]);await loop.poll();assert(trigger,'Actual compiler cancellation trigger was not observed');assert.deepEqual(loop.snapshot().frame,fs.readFileSync(path.join(e,'2-expected.raw')));fs.writeFileSync(path.join(e,'recovered.raw'),loop.snapshot().frame);
  await watcherDone;const verified=await loop.verifyLive();assert.deepEqual(verified.frame,fs.readFileSync(path.join(e,'2-expected.raw')));const events=loop.events();assert.deepEqual(events.filter(row=>row.kind==='published').map(row=>row.generation),[1,3]);
  const failures=builder.failures(),records=builder.records();assert.equal(failures.length,1);assert.equal(records.length,2);assert.match(failures[0].error,/Observed compiler aborted/);assert(failures[0].record?.report?.drained);assert.equal(failures[0].record.report.failure,'abort');assert.equal(failures[0].record.report.remaining_observed,0);assert.equal(failures[0].record.emergencyClosed,false);
  await loop.close();assert.equal(loop.status().liveWorkers,0);assert.equal(loop.status().timers,0);assert.equal(loop.status().building,false);
  fs.writeFileSync(path.join(e,'result.json'),JSON.stringify({qualified:true,trigger,events,records,failures,observations,finalStatus:loop.status(),scope:'Actual owned Rust builds, cooperative supersession, sampled observed cleanup; not universal process quiescence or native Canvas'},null,2)+'\n');
 }catch(error){fs.writeFileSync(path.join(e,'retained-failure.json'),JSON.stringify({qualified:false,error:String(error),trigger,records:builder.records(),failures:builder.failures(),observations,events:loop.events(),status:loop.status(),retryUnchanged:false},null,2)+'\n');throw error;}
 finally{await loop.close();fs.writeFileSync(path.join(e,'closure.json'),JSON.stringify(loop.status(),null,2)+'\n');}
})().catch(error=>{console.error(error);process.exitCode=1;});
