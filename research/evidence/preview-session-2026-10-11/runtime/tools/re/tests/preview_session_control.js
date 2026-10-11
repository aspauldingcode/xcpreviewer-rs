'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {PreviewSession}=require('../reloop/preview_session.js'),{rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const sources=[0,1,2].map(i=>fs.readFileSync(path.join(cfg.input,i+'-source.swift'))),expected=[0,1,2].map(i=>fs.readFileSync(path.join(cfg.input,i+'-expected.raw')));
(async()=>{
 const file=path.join(out,'owned.swift'),write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
 const builder=rustSourceBuilder({...cfg,root:out,oracle:source=>{const i=sources.findIndex(s=>s.equals(source));assert(i>=0);return expected[i];}}),session=new PreviewSession(file,builder),states=[];
 assert.equal(await session.readFrame(),null);assert.equal(session.status().frame,null);
 try{
  write(sources[0]);states.push(await session.start(250,10000));
  const first=await session.readFrame();assert.deepEqual(first.allocation,expected[0]);first.allocation.fill(0);first.descriptor.width=1;const copy=await session.readFrame();assert.deepEqual(copy.allocation,expected[0]);assert.equal(copy.descriptor.width,13);fs.writeFileSync(path.join(out,'0-frame.raw'),copy.allocation);
  write(sources[1]);states.push(await session.poll());const second=await session.readFrame();assert.deepEqual(second.allocation,expected[1]);assert.equal(second.descriptor.width,9);assert.equal(second.descriptor.height,5);assert.equal(second.descriptor.revision,2);fs.writeFileSync(path.join(out,'1-frame.raw'),second.allocation);
  write(Buffer.from('Text("unsupported")'));states.push(await session.poll());assert.deepEqual(session.status().frame,second.descriptor);assert.equal(session.status().diagnostics.lastFailure.kind,'rejected');assert.equal(builder.failures()[0].record.report.target_code,2);
  assert(!JSON.stringify(session.status()).includes('stderr'));assert(!JSON.stringify(session.status()).includes('toolchainPin'));
  const retained=await session.readFrame();assert.deepEqual(retained.allocation,expected[1]);fs.writeFileSync(path.join(out,'retained.raw'),retained.allocation);
  write(sources[2]);states.push(await session.poll());const recovered=await session.readFrame();assert.equal(recovered.descriptor.revision,3);assert.equal(recovered.descriptor.width,13);assert.deepEqual(recovered.allocation,expected[2]);fs.writeFileSync(path.join(out,'2-frame.raw'),recovered.allocation);
  const reading=session.readFrame();await assert.rejects(()=>session.poll(),/operation active/);await reading;
 }finally{await session.close();}
 assert.equal(await session.readFrame(),null);const final=session.status();assert.equal(final.frame,null);assert.equal(final.lifecycle.liveWorkers,0);assert.equal(final.lifecycle.timers,0);assert.equal(final.lifecycle.building,false);
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({states,final,builds:builder.records(),failures:builder.failures(),controls:['empty-read','detached-frame-and-descriptor','geometry-revision-swap','failed-edit-retains-frame','public-status-projection','recovery','concurrent-operation-rejected','close-empty'],scope:'Local consumer API with actual finite Rust compilation; not an MCP server or native Canvas protocol'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
