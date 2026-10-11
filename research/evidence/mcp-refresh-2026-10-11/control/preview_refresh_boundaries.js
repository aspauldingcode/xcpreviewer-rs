// Owned API control: invalid refresh deduplication and cooperative abort.
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const {PreviewSession}=require(process.argv[2]);
(async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'owned-refresh-')),file=path.join(dir,'owned.swift');let builds=0,aborts=0;
 const session=new PreviewSession(file,async(_,{signal})=>{builds++;return new Promise((resolve,reject)=>signal.addEventListener('abort',()=>{aborts++;reject(Error('Owned cooperative abort'));},{once:true}));});
 const states=[];
 try{
  const missing=await session.refresh();assert.equal(missing.readiness.state,'failed');assert.equal(missing.diagnostics.latest.kind,'unavailable-source');states.push(missing);
  assert.deepEqual(await session.refresh(),missing);fs.writeFileSync(file,'');const empty=await session.refresh();assert.equal(empty.readiness.state,'failed');assert.equal(empty.diagnostics.latest.kind,'invalid-source');states.push(empty);assert.deepEqual(await session.refresh(),empty);assert.equal(builds,0);
  fs.writeFileSync(file,'Text("owned")');const pending=session.refresh();assert.equal(builds,1);await assert.rejects(()=>session.refresh(),/operation active/);await session.close();await pending;assert.equal(aborts,1);
  await assert.rejects(()=>session.refresh(),/closed/);assert.equal(await session.readFrame(),null);const final=session.status();assert.equal(final.lifecycle.timers,0);assert.equal(final.lifecycle.liveWorkers,0);assert.equal(final.lifecycle.building,false);
  process.stdout.write(JSON.stringify({states,builds,aborts,final})+'\n');
 }finally{await session.close();fs.rmSync(dir,{recursive:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
