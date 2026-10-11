'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {SourceFileLoop}=require('../reloop/source_file_loop.js');
const input=process.argv[2],out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const rows=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json'))),source=fs.readFileSync(path.join(input,'0-source.swift')),expected=fs.readFileSync(path.join(input,'0-expected.raw'));
const file=path.join(out,'owned.swift'),row=rows[0];const noisy='🔥\n\u0000'.repeat(4000);
const builder=async bytes=>{if(!bytes.equals(source))throw Error(noisy);return {build:{module:fs.readFileSync(path.join(input,'0-view.wasm')),moduleSha256:row.module_sha256,sourceSha256:row.source_sha256,config:row.config,stride:row.stride},expected};};
(async()=>{
 const loop=new SourceFileLoop(file,builder);const write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
 try{
  write(source);await loop.start(250,10000);assert.deepEqual(loop.snapshot().frame,expected);
  for(let i=0;i<80;i++){write(Buffer.from('Unsupported'+i));await loop.poll();}
  const d=loop.diagnostics(),events=loop.events();assert.equal(events.length,64);assert.equal(d.retainedEvents,64);assert.equal(d.droppedEvents,98);
  assert.equal(d.latest.kind,'rejected');assert.equal(d.lastFailure.generation,81);
  const errors=events.filter(e=>e.kind==='rejected').map(e=>e.error);assert.equal(errors.length,32);
  for(const error of errors){assert(Buffer.byteLength(error)<=512);assert(!/[\u0000-\u001f\u007f]/.test(error));assert(error.includes('🔥'));}
  const before=loop.events();d.latest.error='changed';d.lastFailure.error='changed';events[0].kind='changed';assert.deepEqual(loop.events(),before);
  assert.deepEqual(loop.snapshot().frame,expected);assert.deepEqual((await loop.verifyLive()).frame,expected);fs.writeFileSync(path.join(out,'retained.raw'),loop.snapshot().frame);
  write(Buffer.from([255]));await loop.poll();assert.equal(loop.diagnostics().lastFailure.kind,'invalid-source');
  fs.unlinkSync(file);await loop.poll();assert.equal(loop.diagnostics().lastFailure.kind,'unavailable-source');
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({diagnostics:loop.diagnostics(),events:loop.events(),rejected:80,retainedBytes:16384,scope:'Owned prebuilt fixture file-loop bounded diagnostics and retained frame; no fresh compilation or native Canvas evidence'},null,2)+'\n');
 }finally{await loop.close();}
 assert.equal(loop.status().liveWorkers,0);assert.equal(loop.status().timers,0);
})().catch(e=>{console.error(e);process.exitCode=1;});
