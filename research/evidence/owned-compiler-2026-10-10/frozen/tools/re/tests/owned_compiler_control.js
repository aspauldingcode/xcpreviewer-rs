'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {runOwned,compiler}=require('../reloop/owned_compiler.js');const {SourceFileLoop}=require('../reloop/source_file_loop.js');
const config=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const input=config.input,rows=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json'))),sources=rows.map((_,i)=>fs.readFileSync(path.join(input,i+'-source.swift')));
const oracle=source=>{const i=sources.findIndex(s=>s.equals(source));assert(i>=0);return fs.readFileSync(path.join(input,i+'-expected.raw'));};
const builder=compiler({...config,root:path.join(out,'compiler'),oracle});const file=path.join(out,'owned.swift'),write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const loop=new SourceFileLoop(file,builder),records=[];
 try{
  write(sources[0]);await loop.start(25,10000);
  for(let i=0;i<3;i++){
   if(i){write(sources[i]);await loop.poll();}
   const frame=loop.snapshot();assert.equal(frame.revision,i+1);assert.deepEqual(frame.frame,oracle(sources[i]));assert.deepEqual(await loop.verifyLive(),frame);
   assert.equal(frame.moduleSha256,rows[i].module_sha256);fs.writeFileSync(path.join(out,i+'-frame.raw'),frame.frame);records.push({revision:frame.revision,comparedBytes:16384,moduleEqualsPinned:true});
  }
  const baseline=loop.snapshot();write(Buffer.from('Text("unsupported")'));await loop.poll();assert.deepEqual(loop.snapshot(),baseline);assert.deepEqual(await loop.verifyLive(),baseline);assert(loop.events().some(e=>e.kind==='rejected'));await loop.close();assert.equal(loop.status().liveWorkers,0);
 }finally{await loop.close();}
 assert(builder.records().every(r=>!r.cacheHit));
 const controls=[];
 for(const mode of ['timeout','abort']){
  const late=path.join(out,mode+'-late'),a=new AbortController();
  const code='import os,time,sys\nif os.fork()==0:\n time.sleep(0.8)\n open(sys.argv[1],"w").write("late")\nelse:\n print("owned-child-started",flush=True)\n time.sleep(20)\n';
  const task=runOwned(config.python,['-c',code,late],{signal:a.signal,timeout:mode==='timeout'?200:2000});
  let timer;if(mode==='abort')timer=setTimeout(()=>a.abort(),200);
  let error;try{await task;}catch(e){error=e;}finally{clearTimeout(timer);}
  assert(error);assert.match(error.record.stdout,/owned-child-started/);assert.equal(error.record.signal,'SIGKILL');await sleep(900);assert(!fs.existsSync(late));
  controls.push({mode,error:String(error),rootSignal:error.record.signal,childStarted:true,lateWriteAbsent:true});
 }
 fs.writeFileSync(path.join(out,'compiler-result.json'),JSON.stringify({records,builds:builder.records(),controls,unsupportedRetained:true,finalStatus:loop.status(),scope:'Fresh frozen-CLI compilation and owned inherited POSIX group abort/deadline; no detached escaping children or native Canvas semantics'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
