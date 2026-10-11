'use strict';
const assert=require('node:assert/strict'),{PassThrough,Writable}=require('node:stream');
const {servePreview}=require(process.argv[2]);
function peer(session){const input=new PassThrough(),packets=[];const output=new Writable({write(b,_e,cb){packets.push(JSON.parse(b.toString()));cb();}});return {input,packets,done:servePreview(input,output,session,{deadline:500}).done};}
(async()=>{
 let release,closed=false;
 const close=peer({start:()=>new Promise(r=>release=r),close:async()=>{closed=true;release({});},status:()=>({closed})});
 close.input.write('{"id":1,"method":"start"}\n');close.input.write('{"id":2,"method":"close"}\n');const c=await close.done;assert.equal(c.cancelled,1);assert.deepEqual(close.packets,[{id:2,ok:true,result:{closed:true}}]);
 let pending;const queue=peer({start:()=>new Promise(r=>pending=r),close:async()=>pending({}),status:()=>({})});
 for(const [id,method] of [[1,'start'],[2,'status'],[3,'status']])queue.input.write(JSON.stringify({id,method})+'\n');const q=await queue.done;assert.equal(q.cancelled,2);assert.equal(q.reason,'queue-bound');assert.deepEqual(queue.packets,[{id:3,ok:false,error:'queue-bound'}]);
 const pipeline=peer({close:async()=>{},status:()=>({})});pipeline.input.write('{"id":1,"method":"status"}\n{"id":2,"method":"status"}\n');const p=await pipeline.done;assert.equal(p.accepted,0);assert.equal(p.reason,'pipelined-input');assert.deepEqual(pipeline.packets,[]);
})().catch(e=>{console.error(e);process.exitCode=1;});
