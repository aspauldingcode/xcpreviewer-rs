// Owned prebuilt-WASM cancellation control; no native Canvas or fresh compiler claim.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),Module=require('node:module');
const evidence=path.resolve(process.argv[2]),input=path.resolve(process.argv[3]),production=path.resolve(process.argv[4]);
const fixtures=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json'))),sources=fixtures.map((_,i)=>fs.readFileSync(path.join(input,i+'-source.swift')));
const expected=i=>fs.readFileSync(path.join(input,i+'-expected.raw'));
const result=i=>({build:{module:fs.readFileSync(path.join(input,i+'-view.wasm')),moduleSha256:fixtures[i].module_sha256,sourceSha256:fixtures[i].source_sha256,config:fixtures[i].config,stride:fixtures[i].stride},expected:expected(i)});
function implementation(phase){const m=new Module(production,module);m.filename=production;m.paths=Module._nodeModulePaths(path.dirname(production));m._compile(fs.readFileSync(path.join(evidence,'source-file-loop-'+phase+'.js'),'utf8'),production);return m.exports.SourceFileLoop;}
async function control(phase,mode){
 const folder=path.join(evidence,phase+'-'+mode);fs.mkdirSync(folder);const file=path.join(folder,'owned.swift');let release,aborts=0,bCalls=0,started=false;
 const write=source=>{fs.writeFileSync(file+'.tmp',source);fs.renameSync(file+'.tmp',file);};
 const builder=(source,{signal})=>{
  const i=sources.findIndex(s=>s.equals(source));if(i<0)return Promise.reject(Error('Unsupported controlled source'));
  if(i!==1||++bCalls>1)return Promise.resolve(result(i));
  started=true;return new Promise((resolve,reject)=>{const abort=()=>{++aborts;reject(Error('Owned superseded build aborted'));};signal.addEventListener('abort',abort,{once:true});release=()=>{signal.removeEventListener('abort',abort);resolve(result(i));};});
 };
 write(sources[0]);const Loop=implementation(phase),loop=new Loop(file,builder);
 try{
  await loop.poll();const initial=loop.snapshot();assert.deepEqual(initial.frame,expected(0));fs.writeFileSync(path.join(folder,'baseline.raw'),initial.frame);
  write(sources[1]);const old=loop.poll();assert(started&&loop.status().building);
  if(mode==='valid')write(sources[2]);else if(mode==='invalid')write(Buffer.from([255]));else if(mode==='missing')fs.unlinkSync(file);
  const pending=mode==='refresh'?loop.refresh():loop.poll();const cancelledBeforeManualRelease=aborts===1;
  assert.equal(cancelledBeforeManualRelease,phase==='after');
  if(!cancelledBeforeManualRelease)release();
  await pending;await old;
  const final=loop.snapshot(),index=mode==='valid'?2:mode==='refresh'?1:0;
  assert.deepEqual(final.frame,expected(index));assert.deepEqual((await loop.verifyLive()).frame,expected(index));fs.writeFileSync(path.join(folder,'final.raw'),final.frame);
  const events=loop.events();assert(events.some(e=>e.kind==='rejected'));
  await loop.close();assert.equal(loop.status().liveWorkers,0);assert.equal(loop.status().building,false);assert.equal(loop.status().timers,0);
  return {phase,mode,cancelledBeforeManualRelease,aborts,manuallyReleased:!cancelledBeforeManualRelease,accepted:events.filter(e=>e.kind==='published').length,expectedIndex:index,initialRevision:initial.revision,finalRevision:final.revision,events,finalStatus:loop.status()};
 }finally{await loop.close();}
}
(async()=>{const rows=[];for(const phase of ['before','after'])for(const mode of ['valid','invalid','missing','refresh'])rows.push(await control(phase,mode));fs.writeFileSync(path.join(evidence,'results.json'),JSON.stringify(rows,null,2)+'\n');console.log(JSON.stringify(rows.map(r=>({phase:r.phase,mode:r.mode,aborts:r.aborts,accepted:r.accepted}))));})().catch(error=>{console.error(error);process.exitCode=1;});
