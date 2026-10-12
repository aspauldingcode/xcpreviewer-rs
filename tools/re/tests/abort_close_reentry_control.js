// Owned prebuilt-WASM reentrant abort/close ordering control.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),Module=require('node:module');
const evidence=path.resolve(process.argv[2]),input=path.resolve(process.argv[3]),production=path.resolve(process.argv[4]);
const rows=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json'))),sources=rows.map((_,i)=>fs.readFileSync(path.join(input,i+'-source.swift')));
const expected=fs.readFileSync(path.join(input,'0-expected.raw'));
const result={build:{module:fs.readFileSync(path.join(input,'0-view.wasm')),moduleSha256:rows[0].module_sha256,sourceSha256:rows[0].source_sha256,config:rows[0].config,stride:rows[0].stride},expected};
function implementation(phase){const m=new Module(production,module);m.filename=production;m.paths=Module._nodeModulePaths(path.dirname(production));m._compile(fs.readFileSync(path.join(evidence,'source-file-loop-'+phase+'.js'),'utf8'),production);return m.exports.SourceFileLoop;}
async function control(phase,mode){
 const folder=path.join(evidence,phase+'-'+mode);fs.mkdirSync(folder);const file=path.join(folder,'owned.swift');let loop,closePromise,aborts=0,buildCalls=0;
 const write=source=>{fs.writeFileSync(file+'.tmp',source);fs.renameSync(file+'.tmp',file);};
 const builder=(source,{signal})=>{++buildCalls;if(source.equals(sources[0]))return Promise.resolve(result);assert(source.equals(sources[1]));return new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>{++aborts;closePromise=loop.close();reject(Error('Owned abort callback closes loop'));},{once:true}));};
 write(sources[0]);const Loop=implementation(phase);loop=new Loop(file,builder);
 try{
  await loop.poll();const baseline=loop.snapshot();assert.deepEqual(baseline.frame,expected);fs.writeFileSync(path.join(folder,'baseline.raw'),baseline.frame);
  write(sources[1]);const prior=loop.poll();assert(loop.status().building&&buildCalls===2);
  if(mode==='valid')write(sources[2]);else if(mode==='invalid')write(Buffer.from([255]));else if(mode==='missing')fs.unlinkSync(file);
  let observedError=null,pending;
  try{pending=mode==='refresh'?loop.refresh():loop.poll();}catch(error){observedError=error.message;}
  assert.equal(aborts,1);assert(closePromise);await Promise.all([prior,pending,closePromise]);
  if(phase==='before')assert.equal(observedError,'Source host closed');else assert.equal(observedError,null);
  assert.equal(loop.snapshot(),null);assert.equal(buildCalls,2);assert.equal(loop.status().liveWorkers,0);assert.equal(loop.status().building,false);assert.equal(loop.status().timers,0);
  const events=loop.events();assert.equal(events.filter(e=>e.kind==='observed').length,2);assert.equal(events.filter(e=>e.kind==='published').length,1);
  return {phase,mode,observedError,aborts,buildCalls,frameCleared:loop.snapshot()===null,events,finalStatus:loop.status()};
 }finally{await loop.close();}
}
(async()=>{const results=[];for(const phase of ['before','after'])for(const mode of ['valid','invalid','missing','refresh'])results.push(await control(phase,mode));fs.writeFileSync(path.join(evidence,'results.json'),JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify(results.map(r=>({phase:r.phase,mode:r.mode,error:r.observedError,aborts:r.aborts}))));})().catch(error=>{console.error(error);process.exitCode=1;});
