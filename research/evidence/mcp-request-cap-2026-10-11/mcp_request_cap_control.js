const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=process.argv[2],out=process.argv[3],fixed=process.argv[4]==='fixed';const {PreviewSession}=require(path.join(root,'preview_session.js')),{PreviewMcp}=require(path.join(root,'preview_mcp.js'));
const section=(id,v)=>[id,v.length,...v],name=s=>[s.length,...Buffer.from(s)];
function moduleBytes(hang){
 const bodies=[[0,0x41,0x80,0x80,1,0x0b],hang?[0,0x23,0,0x41,1,0x6a,0x24,0,0x23,0,0x41,3,0x4b,0x04,0x40,0x03,0x40,0x0c,0,0x0b,0x0b,0x41,0,0x0b]:[0,0x41,0,0x0b],[0,0x20,0,0x41,4,0x4f,0x20,0,0x41,0x80,2,0x4d,0x71,0x04,0x7f,...(hang?[]:[0,1,2,3].flatMap(i=>[0x41,i,0x41,0xf7,0,0x3a,0,0])),0x20,0,0x05,0x41,0,0x0b,0x0b]];
 return Buffer.from([0,97,115,109,1,0,0,0,...section(1,[2,0x60,0,1,0x7f,0x60,1,0x7f,1,0x7f]),...section(3,[3,0,0,1]),...section(5,[1,1,2,2]),...section(6,[1,0x7f,1,0x41,0,0x0b]),...section(7,[4,...name('capacity'),0,0,...name('pixels'),0,1,...name('render'),0,2,...name('memory'),2,0]),...section(10,[3,...bodies.flatMap(b=>[b.length,...b])])]);
}


(async()=>{const file=path.join(out,'owned.swift'),source=Buffer.from('owned capped session');fs.writeFileSync(file,source);let builds=0;
 const session=new PreviewSession(file,async bytes=>{builds++;const module=moduleBytes(false),expected=Buffer.alloc(16384,0xc3);expected.fill(0x77,0,4);return {build:{module,moduleSha256:crypto.createHash('sha256').update(module).digest('hex'),sourceSha256:crypto.createHash('sha256').update(bytes).digest('hex'),config:{width:1,height:1},stride:64},expected};}),h=new PreviewMcp(session);let id=0;
 const request=(method,params)=>h.handle({jsonrpc:'2.0',id:++id,method,...(params?{params}:{})});let before,atCap,limited,repeated,after,frame;
 try{
  await request('initialize',{protocolVersion:'2025-11-25',capabilities:{},clientInfo:{name:'owned-cap',version:'1'}});await h.handle({jsonrpc:'2.0',method:'notifications/initialized'});const start=await request('tools/call',{name:'preview_start',arguments:{}});assert(!start.result.isError);
  frame=await session.readFrame();fs.writeFileSync(path.join(out,'published.raw'),frame.allocation);before=session.status();
  while(id<256){const p=await request('ping');assert.deepEqual(p.result,{});}assert.equal(h.ids.size,256);atCap=session.status();
  limited=await request('tools/call',{name:'preview_close',arguments:{}});assert.equal(limited.error.code,-32000);after=session.status();
  assert.equal(after.lifecycle.liveWorkers,fixed?0:1);assert.equal(after.lifecycle.timers,fixed?0:2);assert.equal(after.lifecycle.closed,fixed);assert.equal(after.frame===null,fixed);
  if(!fixed){const f=await session.readFrame();fs.writeFileSync(path.join(out,'retained.raw'),f.allocation);}
  repeated=await request('ping');assert.equal(repeated.error.code,-32000);assert.equal(h.ids.size,256);
 }finally{await session.close();}
 const failed=new PreviewMcp({close:async()=>{throw Error('private cleanup secret');}});for(let i=0;i<256;i++)await failed.handle({jsonrpc:'2.0',id:i,method:'ping'});const cleanupFailure=await failed.handle({jsonrpc:'2.0',id:256,method:'ping'});assert.equal(cleanupFailure.error.message,fixed?'Session request limit; cleanup failed':'Session request limit');assert(!JSON.stringify(cleanupFailure).includes('private'));
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({fixed,before,atCap,limited,after,repeated,ids:h.ids.size,builds,cleanupFailure,final:session.status()},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
