'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{PassThrough,Writable}=require('node:stream');
const {servePreview}=require('../reloop/preview_channel.js'),{PreviewSession}=require('../reloop/preview_session.js'),{rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
const sources=[0,1,2].map(i=>fs.readFileSync(path.join(cfg.input,i+'-source.swift'))),expected=[0,1,2].map(i=>fs.readFileSync(path.join(cfg.input,i+'-expected.raw')));
function peer(session,options={}){
 const input=new PassThrough(),packets=[],waiters=[];let text='';const output=new Writable({write(chunk,_encoding,callback){text+=chunk.toString();let n;while((n=text.indexOf('\n'))>=0){const packet=JSON.parse(text.slice(0,n));text=text.slice(n+1);packets.push(packet);waiters.shift()?.(packet);}callback();}});
 const channel=servePreview(input,output,session,options);
 return {input,output,packets,done:channel.done,request:(id,method)=>new Promise(resolve=>{waiters.push(resolve);input.write(JSON.stringify({id,method})+'\n');})};
}
(async()=>{
 const root=path.join(out,'actual');fs.mkdirSync(root);const file=path.join(root,'owned.swift'),write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
 const builder=rustSourceBuilder({...cfg,root,oracle:s=>{const i=sources.findIndex(b=>b.equals(s));assert(i>=0);return expected[i];}}),session=new PreviewSession(file,builder),p=peer(session);
 write(sources[0]);assert((await p.request(1,'start')).ok);const first=await p.request(2,'frame');assert.deepEqual(Buffer.from(first.result.allocationBase64,'base64'),expected[0]);
 write(sources[1]);assert((await p.request(3,'poll')).ok);const second=await p.request(4,'frame');assert.deepEqual(Buffer.from(second.result.allocationBase64,'base64'),expected[1]);assert.equal(second.result.descriptor.width,9);
 assert((await p.request(5,'close')).result.lifecycle.loopClosed);const completed=await p.done;assert.equal(completed.accepted,5);assert.equal(session.status().lifecycle.liveWorkers,0);
 const controls=[];
 const stub=()=>{let closed=false;return {start:async()=>({}),poll:async()=>({}),readFrame:async()=>null,status:()=>({closed}),close:async()=>{closed=true;}};};
 for(const [name,bytes] of [['oversize',Buffer.alloc(4097,65)],['utf8',Buffer.from([255,10])],['extra-key',Buffer.from('{"id":1,"method":"status","extra":1}\n')],['pipeline',Buffer.from('{"id":1,"method":"status"}\n{"id":2,"method":"status"}\n')]]){
  const q=peer(stub());q.input.write(bytes);const result=await q.done;assert.equal(result.rejected,1);assert.equal(result.accepted,0);controls.push({name,result,packets:q.packets});
 }
 const duplicate=peer(stub());await duplicate.request(1,'status');duplicate.input.write('{"id":1,"method":"status"}\n');const dup=await duplicate.done;assert.equal(dup.rejected,1);controls.push({name:'duplicate-id',result:dup,packets:duplicate.packets});
 // Cooperative pending operation: close must cancel and suppress its reply.
 let release,closed=false;const pending={start:()=>new Promise(resolve=>release=resolve),status:()=>({closed}),close:async()=>{closed=true;release?.({});}};
 const cancellation=peer(pending);cancellation.input.write('{"id":1,"method":"start"}\n');await cancellation.request(2,'close');const cancel=await cancellation.done;assert.equal(cancel.cancelled,1);assert.deepEqual(cancellation.packets.map(x=>x.id),[2]);controls.push({name:'close-pending',result:cancel,packets:cancellation.packets});
 let slowClosed=false;const slowIn=new PassThrough(),slowOut=new Writable({highWaterMark:1,write(_chunk,_encoding,_callback){}}),slow={...stub(),close:async()=>{slowClosed=true;}};
 const slowChannel=servePreview(slowIn,slowOut,slow,{deadline:500,writeDeadline:50});slowIn.write('{"id":1,"method":"status"}\n');const backpressure=await slowChannel.done;assert(slowClosed);assert.equal(slowOut.listenerCount('drain'),0);assert.equal(backpressure.rejected,1);controls.push({name:'backpressure-deadline',result:backpressure,packets:[]});
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({actual:{packets:p.packets,completed,builds:builder.records(),failures:builder.failures(),final:session.status()},controls,scope:'Owned NDJSON channel, actual finite Rust positive frames; synthetic cooperative close/backpressure, not MCP/native Canvas'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
