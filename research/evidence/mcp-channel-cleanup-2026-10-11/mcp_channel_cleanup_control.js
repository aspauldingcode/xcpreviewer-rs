const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),{PassThrough}=require('node:stream');
const root=process.argv[2],out=process.argv[3],fixed=process.argv[4]==='fixed';const {PreviewSession}=require(path.join(root,'preview_session.js')),{PreviewMcp}=require(path.join(root,'preview_mcp.js')),{serveMcp}=require(path.join(root,'mcp_channel.js'));
const section=(id,v)=>[id,v.length,...v],name=s=>[s.length,...Buffer.from(s)];
function moduleBytes(hang){
 const bodies=[[0,0x41,0x80,0x80,1,0x0b],hang?[0,0x23,0,0x41,1,0x6a,0x24,0,0x23,0,0x41,3,0x4b,0x04,0x40,0x03,0x40,0x0c,0,0x0b,0x0b,0x41,0,0x0b]:[0,0x41,0,0x0b],[0,0x20,0,0x41,4,0x4f,0x20,0,0x41,0x80,2,0x4d,0x71,0x04,0x7f,...(hang?[]:[0,1,2,3].flatMap(i=>[0x41,i,0x41,0xf7,0,0x3a,0,0])),0x20,0,0x05,0x41,0,0x0b,0x0b]];
 return Buffer.from([0,97,115,109,1,0,0,0,...section(1,[2,0x60,0,1,0x7f,0x60,1,0x7f,1,0x7f]),...section(3,[3,0,0,1]),...section(5,[1,1,2,2]),...section(6,[1,0x7f,1,0x41,0,0x0b]),...section(7,[4,...name('capacity'),0,0,...name('pixels'),0,1,...name('render'),0,2,...name('memory'),2,0]),...section(10,[3,...bodies.flatMap(b=>[b.length,...b])])]);
}


(async()=>{const rows=[];
 for(const kind of ['complete','before-release','after-release']){
  const dir=path.join(out,kind);fs.mkdirSync(dir);const file=path.join(dir,'owned.swift');fs.writeFileSync(file,'owned cleanup boundary');let builds=0,closeCalls=0;
  const session=new PreviewSession(file,async bytes=>{builds++;const module=moduleBytes(false),expected=Buffer.alloc(16384,0xc3);expected.fill(0x77,0,4);return {build:{module,moduleSha256:crypto.createHash('sha256').update(module).digest('hex'),sourceSha256:crypto.createHash('sha256').update(bytes).digest('hex'),config:{width:1,height:1},stride:64},expected};});let summary,before,after,wire='';
  try{
   await session.start(250,10000);const f=await session.readFrame();fs.writeFileSync(path.join(dir,'published.raw'),f.allocation);before=session.status();
   const input=new PassThrough(),output=new PassThrough();let received;const packet=new Promise(r=>received=r);output.on('data',b=>{wire+=b.toString();if(wire.includes('\n'))received();});
   const adapter={close:async()=>{closeCalls++;if(kind==='before-release')throw Error('private failure before release');await session.close();if(kind==='after-release')throw Error('private failure after release');}};
   const channel=serveMcp(input,output,new PreviewMcp(session),adapter,{deadline:500,writeDeadline:50});input.write(JSON.stringify({jsonrpc:'2.0',id:1,method:'ping'})+'\n');await packet;input.end();summary=await channel.done;after=session.status();
   assert.equal(summary.closed,true);assert.equal(summary.reason,'input-ended');assert.equal(closeCalls,1);assert.equal(summary.received,1);assert.equal(summary.writes,1);assert.equal(summary.suppressed,0);
   if(fixed)assert.equal(summary.cleanup,kind==='complete'?'complete':'failed');else assert.equal(summary.cleanup,undefined);
   assert.equal(after.lifecycle.liveWorkers,kind==='before-release'?1:0);assert.equal(after.frame!==null,kind==='before-release');
   if(kind==='before-release'){const f=await session.readFrame();fs.writeFileSync(path.join(dir,'retained.raw'),f.allocation);}
   assert.deepEqual(JSON.parse(wire),{jsonrpc:'2.0',id:1,result:{}});assert(!JSON.stringify(summary).includes('private'));
  }finally{await session.close();}
  rows.push({kind,before,after,summary,closeCalls,builds,wire,final:session.status()});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({fixed,rows},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
