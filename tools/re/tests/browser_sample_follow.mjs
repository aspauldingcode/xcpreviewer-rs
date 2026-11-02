import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {webcrypto} from 'node:crypto';
globalThis.crypto??=webcrypto;
const path=new URL('../browser-preview/sample-follow.js',import.meta.url);
const source=await readFile(path,'utf8');
const {createSampleFollower,createSampleReader}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function harness(read){const applied=[],errors=[],scheduled=[];let canceled=0;const f=createSampleFollower({read,apply:x=>applied.push(x),failed:e=>errors.push(e.message),schedule:fn=>{scheduled.push(fn);return fn},cancel:()=>canceled++});return{f,applied,errors,scheduled,get canceled(){return canceled}}}
function frame(fingerprint){return {fingerprint,buffer:fingerprint}}
const passed=[];
{
 let count=0;const h=harness(async()=>frame(count<2?'a':'b'));
 h.f.start();await flush();assert.deepEqual(h.applied,['a']);
 count++;h.scheduled.shift()();await flush();assert.deepEqual(h.applied,['a']);
 count++;h.scheduled.shift()();await flush();assert.deepEqual(h.applied,['a','b']);h.f.stop();passed.push('unchanged bytes skip decode; changed bytes apply');
}
{
 let finish;const h=harness(()=>new Promise(resolve=>finish=resolve));h.f.start();h.f.stop();finish(frame('late'));await flush();assert.deepEqual(h.applied,[]);assert.equal(h.scheduled.length,0);passed.push('stopped in-flight read cannot update or reschedule');
}
{
 const pending=[];const read=()=>new Promise(resolve=>pending.push(resolve));let aborts=0;read.abort=()=>aborts++;const h=harness(read);h.f.start();h.f.start();pending[0](frame('old'));pending[1](frame('new'));await flush();assert.deepEqual(h.applied,['new']);assert.equal(h.scheduled.length,1);assert.equal(aborts,2);h.f.stop();passed.push('restart rejects old epoch and aborts reader');
}
{
 let state=0;const h=harness(async()=>{if(state===1)throw Error('unavailable');return frame('good')});h.f.start();await flush();state=1;h.scheduled.shift()();await flush();h.scheduled.shift()();await flush();assert.deepEqual(h.errors,['unavailable']);assert.deepEqual(h.applied,['good']);state=2;h.scheduled.shift()();await flush();assert.deepEqual(h.applied,['good','good']);h.f.stop();passed.push('failure preserves frame; deduplicates error; recovery restores status');
}
{
 const reader=createSampleReader(async(url,options)=>{assert.equal(url,'./sample.bplist');assert.equal(options.cache,'no-store');return{ok:true,arrayBuffer:async()=>new Uint8Array([1,2,3]).buffer}});const a=await reader(),b=await reader();assert.equal(a.fingerprint,b.fingerprint);assert.equal(a.fingerprint,'039058c6f2c0cb492c533b0a4d14ef77cc0f78abccced5287d84a1a2011cfb81');
 await assert.rejects(createSampleReader(async()=>({ok:false}))(),/Sample unavailable/);
 await assert.rejects(createSampleReader(async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(64*1024*1024+1)}))(),/exceeds 64 MiB/);passed.push('reader hashes bytes; rejects HTTP and oversized data');
}
{
 let started;const ready=new Promise(resolve=>started=resolve);const reader=createSampleReader(async(_,options)=>new Promise((resolve,reject)=>{options.signal.addEventListener('abort',()=>reject(Error('aborted')));started()}));const result=reader();await ready;reader.abort();await assert.rejects(result,/aborted/);passed.push('reader abort cancels active fetch');
}
console.log(JSON.stringify({passed:true,controls:passed.length,checks:passed}));
