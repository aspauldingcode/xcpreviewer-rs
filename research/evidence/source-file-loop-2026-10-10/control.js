'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {SourceFileLoop}=require('../reloop/source_file_loop.js');
const input=process.argv[2],out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const rows=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json'))),sources=rows.map((_,i)=>fs.readFileSync(path.join(input,i+'-source.swift')));
const expected=i=>fs.readFileSync(path.join(input,i+'-expected.raw'));
const build=i=>({module:fs.readFileSync(path.join(input,i+'-view.wasm')),moduleSha256:rows[i].module_sha256,sourceSha256:rows[i].source_sha256,config:rows[i].config,stride:rows[i].stride});
const file=path.join(out,'owned.swift');let release,delayed=false,aborts=0;
function builder(source,{signal}){
 const i=sources.findIndex(s=>s.equals(source));if(i<0)return Promise.reject(Error('Unsupported source fixture'));
 if(i!==1)return Promise.resolve({build:build(i),expected:expected(i)});
 delayed=true;return new Promise((resolve,reject)=>{
  const abort=()=>{++aborts;reject(Error('Owned builder aborted'));};
  signal.addEventListener('abort',abort,{once:true});
  release=()=>{signal.removeEventListener('abort',abort);resolve({build:build(i),expected:expected(i)});};
 });
}
const write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
const wait=async predicate=>{const deadline=Date.now()+2000;while(!predicate()){assert(Date.now()<deadline,'Owned watcher deadline');await new Promise(r=>setTimeout(r,10));}};
(async()=>{
 write(sources[0]);const loop=new SourceFileLoop(file,builder),controls=[];
 try{
  await loop.start(10,5000);let baseline=loop.snapshot();assert.deepEqual(baseline.frame,expected(0));assert.deepEqual(await loop.verifyLive(),baseline);
  await new Promise(r=>setTimeout(r,30));assert.equal(loop.events().filter(e=>e.kind==='published').length,1);controls.push('unchanged-file-skipped');
  write(sources[1]);await wait(()=>delayed);write(sources[2]);await wait(()=>loop.events().filter(e=>e.kind==='observed').length===3);release();
  await wait(()=>loop.snapshot()?.revision===2 && !loop.status().building && !loop.status().busy);baseline=loop.snapshot();assert.deepEqual(baseline.frame,expected(2));assert.deepEqual(await loop.verifyLive(),baseline);assert(loop.events().some(e=>e.kind==='rejected'&&/Stale/.test(e.error)));controls.push('superseded-build-retained');
  for(const [name,bytes] of [['unsupported',Buffer.from('Text("unsupported")')],['non-ascii',Buffer.from([255])],['oversized',Buffer.alloc(5000,65)]]){
   write(bytes);await loop.poll();assert.deepEqual(loop.snapshot(),baseline);assert.deepEqual(await loop.verifyLive(),baseline);controls.push(name+'-retained');
  }
  fs.unlinkSync(file);await loop.poll();assert.deepEqual(loop.snapshot(),baseline);assert.deepEqual(await loop.verifyLive(),baseline);controls.push('deleted-retained');
  write(sources[0]);await loop.poll();assert.equal(loop.snapshot().revision,3);assert.deepEqual(loop.snapshot().frame,expected(0));
  fs.writeFileSync(path.join(out,'last-frame.raw'),loop.snapshot().frame);
  delayed=false;write(sources[1]);loop.poll();await wait(()=>delayed);await Promise.all([loop.close(),loop.close()]);
  assert.equal(aborts,1);assert.equal(loop.snapshot(),null);assert.equal(loop.status().timers,0);assert.equal(loop.status().building,false);assert.equal(loop.status().liveWorkers,0);controls.push('close-aborted-builder');
  const events=loop.events();await new Promise(r=>setTimeout(r,30));assert.deepEqual(loop.events(),events);
  let deadlineAborts=0;
  const deadlineLoop=new SourceFileLoop(file,(_source,{signal})=>new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>{++deadlineAborts;reject(Error('Owned deadline abort'));},{once:true})));
  deadlineLoop.start(10,500);await wait(()=>deadlineLoop.status().loopClosed && !deadlineLoop.status().building);
  await deadlineLoop.close();assert.equal(deadlineAborts,1);assert.equal(deadlineLoop.status().timers,0);assert.equal(deadlineLoop.status().liveWorkers,0);
  fs.writeFileSync(path.join(out,'file-loop-result.json'),JSON.stringify({controls,events,deadlineAborts,accepted:events.filter(e=>e.kind==='published').length,aborts,final_status:loop.status(),full_allocation_compared:true,source_mode:'Actual bounded file polling and atomic replacements; prebuilt pinned fixture adapter, no fresh compilation',scope:'Owned file/reconstruction policy, not native Canvas edits/state migration'},null,2)+'\n');
 }finally{await loop.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
