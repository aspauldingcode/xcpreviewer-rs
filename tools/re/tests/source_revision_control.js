'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {SourceRevisionHost}=require('../reloop/source_revision_host.js');
const input=process.argv[2],out=process.argv[3]||input;
const fixtures=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json')));
const source=i=>fs.readFileSync(path.join(input,i+'-source.swift'));
const frame=i=>fs.readFileSync(path.join(input,i+'-expected.raw'));
const build=i=>({module:fs.readFileSync(path.join(input,i+'-view.wasm')),moduleSha256:fixtures[i].module_sha256,
 sourceSha256:fixtures[i].source_sha256,config:fixtures[i].config,stride:fixtures[i].stride});
(async()=>{
 const host=new SourceRevisionHost(),controls=[];
 try{
  const a=host.begin(source(0)),first=await host.submit(a,build(0),frame(0));
  assert.equal(first.sourceRevision.sourceSha256,fixtures[0].source_sha256);
  first.sourceRevision.sourceSha256='changed';assert.equal(host.snapshot().sourceRevision.sourceSha256,a.sourceSha256);
  const baseline=host.snapshot();
  const b=host.begin(source(1)),c=host.begin(source(2));
  assert.throws(()=>host.submit(b,build(1),frame(1)),/Stale/);assert.deepEqual(host.snapshot(),baseline);controls.push('stale-completed-build');
  assert.throws(()=>host.submit({...c},build(2),frame(2)),/foreign/);controls.push('foreign-ticket');
  assert.throws(()=>host.submit(c,build(1),frame(1)),/source receipt/);controls.push('source-receipt-mismatch');
  const wrong=build(2);wrong.moduleSha256='0'.repeat(64);assert.throws(()=>host.submit(c,wrong,frame(2)),/module receipt/);controls.push('module-receipt-mismatch');
  const pending=host.submit(c,build(2),frame(2));host.begin(Buffer.from('Text("unsupported")'));
  await assert.rejects(pending,/superseded/);assert.deepEqual(host.snapshot(),baseline);assert.deepEqual(await host.verifyLive(),baseline);assert.equal(host.status().liveWorkers,1);controls.push('superseded-in-flight-candidate');
  const recovery=host.begin(source(2)),second=await host.submit(recovery,build(2),frame(2));assert.equal(second.revision,2);assert.equal(second.sourceRevision.generation,5);assert.deepEqual(second.frame,frame(2));
  const reversal=host.begin(source(0)),third=await host.submit(reversal,build(0),frame(0));assert.equal(third.revision,3);assert.equal(third.sourceRevision.generation,6);assert.deepEqual(third.frame,frame(0));assert.deepEqual(await host.verifyLive(),third);
  await host.close();assert.equal(host.status().liveWorkers,0);assert.throws(()=>host.begin(source(0)),/closed/);
  fs.writeFileSync(path.join(out,'source-result.json'),JSON.stringify({node:process.version,v8:process.versions.v8,accepted_revisions:3,source_generations:6,controls,retained_bytes:16384,final_status:host.status(),source_frame_provenance_atomic:true,scope:'Owned source-generation/build receipt consistency; not native sequence/state migration or provenance authenticity'},null,2)+'\n');
 }finally{await host.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
