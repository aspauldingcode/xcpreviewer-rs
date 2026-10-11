const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=process.argv[2],out=process.argv[3],fixed=process.argv[4]==='fixed';
const {PreviewSession}=require(path.join(root,'preview_session.js')),{PreviewMcp}=require(path.join(root,'preview_mcp.js')),{PreviewConsumer}=require(path.join(root,'preview_consumer.js'));
const section=(id,v)=>[id,v.length,...v],name=s=>[s.length,...Buffer.from(s)];
function moduleBytes(hang){
 const bodies=[[0,0x41,0x80,0x80,1,0x0b],hang?[0,0x23,0,0x41,1,0x6a,0x24,0,0x23,0,0x41,3,0x4b,0x04,0x40,0x03,0x40,0x0c,0,0x0b,0x0b,0x41,0,0x0b]:[0,0x41,0,0x0b],[0,0x20,0,0x41,4,0x4f,0x20,0,0x41,0x80,2,0x4d,0x71,0x04,0x7f,...(hang?[]:[0,1,2,3].flatMap(i=>[0x41,i,0x41,0xf7,0,0x3a,0,0])),0x20,0,0x05,0x41,0,0x0b,0x0b]];
 return Buffer.from([0,97,115,109,1,0,0,0,...section(1,[2,0x60,0,1,0x7f,0x60,1,0x7f,1,0x7f]),...section(3,[3,0,0,1]),...section(5,[1,1,2,2]),...section(6,[1,0x7f,1,0x41,0,0x0b]),...section(7,[4,...name('capacity'),0,0,...name('pixels'),0,1,...name('render'),0,2,...name('memory'),2,0]),...section(10,[3,...bodies.flatMap(b=>[b.length,...b])])]);
}

(async()=>{
 const source=Buffer.from('owned host fixture'),file=path.join(out,'owned.swift');fs.writeFileSync(file,source);let builds=0;
 const builder=async bytes=>{const hang=++builds===1,module=moduleBytes(hang),expected=Buffer.alloc(16384,0xc3);if(!hang)expected.fill(0x77,0,4);return {build:{module,moduleSha256:crypto.createHash('sha256').update(module).digest('hex'),sourceSha256:crypto.createHash('sha256').update(bytes).digest('hex'),config:{width:1,height:1},stride:64},expected};};
 const session=new PreviewSession(file,builder),mcp=new PreviewMcp(session),packets=[];let id=0;const call=async name=>{const p=await mcp.handle({jsonrpc:'2.0',id:++id,method:'tools/call',params:{name:'preview_'+name,arguments:{}}});packets.push({name,packet:p});return p.result;};
 await mcp.handle({jsonrpc:'2.0',id:++id,method:'initialize',params:{protocolVersion:'2025-11-25',capabilities:{},clientInfo:{name:'owned-quarantine',version:'1'}}});await mcp.handle({jsonrpc:'2.0',method:'notifications/initialized'});
 const consumer=new PreviewConsumer(async r=>call(r.name.slice(8)));let states=[],failure,error;
 try{
 await call('start');const first=await consumer.sample();assert.equal(first.status.readiness.state,'ready');fs.writeFileSync(path.join(out,'first.raw'),first.frame.allocation);
 failure=await call('frame');assert.equal(failure.isError,true);const rawStatus=session.status();assert.equal(rawStatus.lifecycle.liveWorkers,0);const before=packets.length;
 try{const stale=await consumer.sample();states.push(stale.status);fs.writeFileSync(path.join(out,'retained.raw'),stale.frame.allocation);assert.equal(stale.status.readiness.state,'stale');assert.equal(stale.status.frame.revision,1);}catch(e){error=String(e);if(fixed)throw e;fs.writeFileSync(path.join(out,'retained.raw'),consumer.snapshot().frame.allocation);}
 const quarantineCalls=packets.length-before;if(fixed){assert.equal(quarantineCalls,2);assert(!error);}else{assert(error);assert.equal(rawStatus.readiness.state,'ready');}
 await call('refresh');const recovered=await consumer.sample();assert.equal(recovered.status.readiness.state,'ready');assert.equal(recovered.status.frame.revision,2);assert.equal(recovered.status.frame.generation,2);fs.writeFileSync(path.join(out,'recovered.raw'),recovered.frame.allocation);states.push(recovered.status);
 await call('close');const closed=await consumer.sample();assert.equal(closed.frame,null);const calls=packets.length;await consumer.sample();assert.equal(packets.length,calls);
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({fixed,raw_status:rawStatus,quarantine_calls:quarantineCalls,error:error||null,states,final:session.status(),consumer_final:closed.status,builds,packets},null,2)+'\n');
 }finally{await session.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
