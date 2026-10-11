'use strict';
// Bounded stdio framing around PreviewMcp. Trusted session.close must settle.
function serveMcp(input,output,handler,session,{deadline=10000,writeDeadline=1000}={}){
 if(!Number.isSafeInteger(deadline)||deadline<500||deadline>10000||!Number.isSafeInteger(writeDeadline)||writeDeadline<50||writeDeadline>1000)throw Error('Deadline bounds');
 const hasId=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&'id'in x;
 let buffer=Buffer.alloc(0),queue=[],active=null,task=null,stopped=false,received=0,writes=0,suppressed=0,closePromise=null,resolveDone;
 const done=new Promise(r=>resolveDone=r),timer=setTimeout(()=>{void stop('channel-deadline');},deadline);
 const closeSession=()=>closePromise||(closePromise=Promise.resolve().then(()=>session.close()));
 async function write(packet){
  const bytes=Buffer.from(JSON.stringify(packet)+'\n');if(bytes.length>32768)throw Error('Response bound');++writes;
  if(!output.write(bytes))await new Promise((resolve,reject)=>{
   const finish=error=>{clearTimeout(t);output.off('drain',drain);output.off('error',fail);error?reject(error):resolve();};
   const drain=()=>finish(),fail=e=>finish(e),t=setTimeout(()=>finish(Error('Write deadline')),writeDeadline);output.once('drain',drain);output.once('error',fail);
  });
 }
 async function stop(reason){
  if(stopped)return;stopped=true;clearTimeout(timer);buffer=Buffer.alloc(0);input.off('data',data);input.destroy();
  if(active&&!active.writing&&!active.cancelled&&hasId(active.message)){active.cancelled=true;++suppressed;}
  suppressed+=queue.filter(x=>hasId(x.message)).length;queue=[];
  try{await closeSession();if(task)await task;output.end();}catch(_){output.destroy();}
  finally{resolveDone({received,writes,suppressed,closed:true,reason});}
 }
 async function pump(){
  while(!stopped&&queue.length){
   active=queue.shift();const current=active;
   try{
    const packet=current.parseError?{jsonrpc:'2.0',id:null,error:{code:-32700,message:'Parse error'}}:await handler.handle(current.message);
    if(packet&&!stopped&&!current.cancelled){current.writing=true;await write(packet);}
   }catch(_){void stop('output-failed');}
   finally{active=null;}
  }
  task=null;
 }
 function cancellation(m){
  if(!m||m.jsonrpc!=='2.0'||m.method!=='notifications/cancelled'||'id'in m)return false;
  const p=m.params;if(!p||typeof p!=='object'||Array.isArray(p)||!('requestId'in p)||('reason'in p&&typeof p.reason!=='string'))return true;
  if(active&&active.message&&active.message.id===p.requestId&&active.message.method==='tools/call'&&!active.writing&&!active.cancelled){
   active.cancelled=true;++suppressed;void closeSession().catch(()=>{void stop('close-failed');});
  }
  const index=queue.findIndex(x=>hasId(x.message)&&x.message.id===p.requestId&&x.message.method!=='initialize');
  if(index>=0){const m=queue.splice(index,1)[0].message;++suppressed;if(handler.ids.size<256)handler.ids.add(typeof m.id+':'+m.id);}
  return true;
 }
 function enqueue(item){if(queue.length>=8){void stop('queue-bound');return;}queue.push(item);if(!task)task=pump();}
 function data(chunk){
  if(stopped)return;if(!Buffer.isBuffer(chunk))chunk=Buffer.from(chunk);if(chunk.length>65536){void stop('chunk-bound');return;}
  buffer=Buffer.concat([buffer,chunk]);
  while(!stopped){const n=buffer.indexOf(10);if(n<0){if(buffer.length>4096)void stop('request-bound');break;}if(n>4096){void stop('request-bound');break;}
   const line=buffer.subarray(0,n);buffer=buffer.subarray(n+1);const text=line.toString('utf8');if(!Buffer.from(text).equals(line)){void stop('invalid-utf8');break;}
   let m;try{m=JSON.parse(text);}catch(_){enqueue({parseError:true});continue;}
   ++received;if(!cancellation(m))enqueue({message:m,cancelled:false,writing:false});
  }
 }
 input.on('data',data);input.once('end',()=>{void stop('input-ended');});input.once('error',()=>{void stop('input-error');});output.once('error',()=>{void stop('output-error');});
 return {done};
}
module.exports={serveMcp};
