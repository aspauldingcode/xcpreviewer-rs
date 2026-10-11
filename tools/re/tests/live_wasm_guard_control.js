'use strict';
// Deliberate synchronous callback reentrancy, distinct from native Canvas policy.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {LiveWasmHost}=require(process.argv[3] || '../reloop/live_wasm_host.js');
const dir=process.argv[2],observe=process.argv[4]==='observe';
const fixture=process.argv[5] || path.resolve(__dirname,'../../../research/evidence/live-wasm-swap-2026-10-10');
const row=JSON.parse(fs.readFileSync(path.join(fixture,'fixtures.json')))[0];
const moduleBytes=fs.readFileSync(path.join(fixture,'0-view.wasm'));
const expected=fs.readFileSync(path.join(fixture,'0-allocation.raw'));
const propose=(host,guard=()=>true)=>host.propose(moduleBytes,expected,row.config.width,row.config.height,row.stride,1500,guard);
(async()=>{
 const controls=[];
 for(const active of [false,true]){
  const host=new LiveWasmHost();let close;
  try{
   if(active){const initial=await propose(host);assert.deepEqual(initial.frame,expected);assert.deepEqual(await host.verifyLive(),initial);}
   const revision=host.status().revision;
   let error;try{await propose(host,()=>{close=host.close();return true;});}catch(e){error=String(e);}
   assert(error);await close;
   const status=host.status(),snapshot=host.snapshot();
   const passed=snapshot===null && status.revision===revision && status.liveWorkers===0 && status.closed && !status.busy;
   controls.push({case:active?'close-in-guard-active':'close-in-guard-empty',error,revision_before:revision,status,
    snapshot_after_close:snapshot===null?'null':'published',allocation_bytes:active?16384:0,passed});
   if(!observe)assert(passed,'Reentrant close published a closed-host snapshot or advanced revision');
   await host.close();
  }finally{await host.close();}
 }
 const host=new LiveWasmHost();
 try{
  const baseline=await propose(host);
  for(const [name,guard] of [['false',()=>false],['throw',()=>{throw Error('Owned guard failure');}],['promise',()=>Promise.resolve(true)]]){
   await assert.rejects(propose(host,guard));assert.deepEqual(host.snapshot(),baseline);assert.deepEqual(await host.verifyLive(),baseline);assert.equal(host.status().liveWorkers,1);
   controls.push({case:'guard-'+name,passed:true,allocation_bytes:16384,retained_revision:baseline.revision});
  }
 }finally{await host.close();}
 assert.equal(host.status().liveWorkers,0);
 fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,'guard-result.json'),JSON.stringify({controls,failures:controls.filter(c=>!c.passed).length,scope:'Owned callback reentrancy and closed-host invariants; no native Canvas state policy.'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
