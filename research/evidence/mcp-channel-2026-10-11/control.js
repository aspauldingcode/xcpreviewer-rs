'use strict';
const {PassThrough,Writable}=require('node:stream');
const {PreviewMcp}=require(process.argv[2]),{serveMcp}=require(process.argv[3]);
const wire=m=>Buffer.from(JSON.stringify(m)+'\n');
const req=(id,method,params)=>({jsonrpc:'2.0',id,method,...(params===undefined?{}:{params})});
const init=req('init','initialize',{protocolVersion:'2025-11-25',capabilities:{},clientInfo:{name:'ø-control',version:'1'}});
const initialized={jsonrpc:'2.0',method:'notifications/initialized'};
const cancel=id=>({jsonrpc:'2.0',method:'notifications/cancelled',params:{requestId:id}});
function fixture(block=false,backpressure=false){
 const input=new PassThrough(),output=backpressure?new Writable({highWaterMark:1,write(_c,_e,_cb){}}):new PassThrough();let buffer='',closed=false,pending=false,release,entered;
 const started=new Promise(r=>entered=r),packets=[],waiters=[];
 if(!backpressure)output.on('data',b=>{buffer+=b.toString();for(;;){const n=buffer.indexOf('\n');if(n<0)break;packets.push(JSON.parse(buffer.slice(0,n)));buffer=buffer.slice(n+1);while(waiters.length)waiters.shift()();}});
 const session={async start(){if(block){pending=true;entered();await new Promise(r=>release=r);pending=false;}return {ready:!closed};},async poll(){return {closed};},status(){return {closed,pending};},async readFrame(){return {descriptor:{revision:1},allocation:Buffer.from(Array.from({length:16384},(_,i)=>(i*19+7)&255))};},async close(){closed=true;if(release)release();}};
 const h=new PreviewMcp(session),channel=serveMcp(input,output,h,session,{deadline:500,writeDeadline:50});
 const wait=async n=>{while(packets.length<n)await new Promise(r=>waiters.push(r));};
 return {input,output,packets,wait,started,session,h,channel,summary:()=>({closed,pending})};
}
(async()=>{
 const controls=[];
 const f=fixture();const bytes=wire(init);for(const b of bytes)f.input.write(Buffer.from([b]));await f.wait(1);
 f.input.write(Buffer.concat([wire(initialized),wire(req(0,'tools/list'))]));await f.wait(2);
 f.input.write(wire(req('frame','tools/call',{name:'preview_frame'})));await f.wait(3);f.input.write(Buffer.from('{\n'));await f.wait(4);f.input.write(wire(req(1,'ping')));await f.wait(5);f.input.end();controls.push({name:'normal',packets:f.packets,result:await f.channel.done,final:f.summary()});
 for(const name of ['cancel','eof','queue']){
  const x=fixture(true);x.input.write(wire(init));await x.wait(1);x.input.write(wire(initialized));x.input.write(wire(req(3,'tools/call',{name:'preview_start'})));await x.started;
  if(name==='cancel'){
   x.input.write(wire(cancel('unknown')));x.input.write(wire(req(4,'preview_unknown')));x.input.write(wire(cancel(4)));x.input.write(wire(cancel(3)));x.input.write(wire(req(4,'ping')));await x.wait(2);x.input.end();
  }else if(name==='queue'){for(let i=0;i<9;i++)x.input.write(wire(req(10+i,'ping')));}else x.input.end();
  controls.push({name,packets:x.packets,result:await x.channel.done,final:x.summary()});
 }
 for(const name of ['size','utf8','chunk','deadline','backpressure','json-eof']){
  const x=fixture(false,name==='backpressure');
  if(name==='size')x.input.write(Buffer.alloc(4097,65));
  else if(name==='utf8')x.input.write(Buffer.from([255,10]));
  else if(name==='chunk')x.input.write(Buffer.alloc(65537,65));
  else if(name==='json-eof'){x.input.write(Buffer.from('1\n'));x.input.end();}
  else if(name==='backpressure')x.input.write(wire(init));
  controls.push({name,packets:x.packets,result:await x.channel.done,final:x.summary()});
 }
 process.stdout.write(JSON.stringify({controls})+'\n');
})().catch(e=>{process.stderr.write(String(e));process.exitCode=1;});
