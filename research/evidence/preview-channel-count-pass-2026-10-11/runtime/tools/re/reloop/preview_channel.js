'use strict';
// Owned NDJSON transport v1; not JSON-RPC or MCP.
function servePreview(input,output,session,{deadline=10000,writeDeadline=1000}={}){
 if(!Number.isSafeInteger(deadline)||deadline<500||deadline>10000||!Number.isSafeInteger(writeDeadline)||writeDeadline<50||writeDeadline>1000)throw Error('Channel deadline bounds');
 let buffer=Buffer.alloc(0),busy=false,stopped=false,lastId=0,queued=null,responseStarted=false,cancelled=0,accepted=0,rejected=0,writes=0,task=null,resolveDone;
 const done=new Promise(resolve=>resolveDone=resolve),timer=setTimeout(()=>{void stop(null,'channel-deadline');},deadline);
 async function write(value){
  const bytes=Buffer.from(JSON.stringify(value)+'\n');if(bytes.length>32768)throw Error('Response bound');
  ++writes;if(!output.write(bytes)){
   await new Promise((resolve,reject)=>{
    const finish=error=>{clearTimeout(timeout);output.off('drain',drain);output.off('error',fail);error?reject(error):resolve();};
    const drain=()=>finish(),fail=error=>finish(error),timeout=setTimeout(()=>finish(Error('Write deadline')),writeDeadline);
    output.once('drain',drain);output.once('error',fail);
   });
  }
 }
 async function stop(id,error){
  if(stopped)return;stopped=true;clearTimeout(timer);buffer=Buffer.alloc(0);input.off('data',onData);input.pause();
  if(busy&&!responseStarted)++cancelled;if(queued){++cancelled;queued=null;}
  try{await session.close();if(task)await task;if(id!==null)await write(error?{id,ok:false,error}:{id,ok:true,result:session.status()});output.end();}
  catch(_){output.destroy();}
  finally{resolveDone({accepted,rejected,cancelled,writes,closed:true,reason:error});}
 }
 async function dispatch(request){
  busy=true;responseStarted=false;
  try{
   let result;
   if(request.method==='start')result=await session.start(250,deadline);
   else if(request.method==='poll')result=await session.poll();
   else if(request.method==='status')result=session.status();
   else {const frame=await session.readFrame();result=frame?{descriptor:frame.descriptor,allocationBase64:frame.allocation.toString('base64')}:null;}
   if(!stopped){responseStarted=true;await write({id:request.id,ok:true,result});}
  }catch(_){if(!stopped){++rejected;try{responseStarted=true;await write({id:request.id,ok:false,error:'operation-failed'});}catch(_){void stop(null,'output-failed');}}}
  finally{busy=false;if(!stopped&&queued){const next=queued;queued=null;task=dispatch(next);}}
 }
 function reject(id,code){++rejected;void stop(id,code);}
 function onData(chunk){
  if(stopped)return;if(!Buffer.isBuffer(chunk))chunk=Buffer.from(chunk);
  if(buffer.length+chunk.length>4096){reject(null,'request-bound');return;}
  buffer=Buffer.concat([buffer,chunk]);const newline=buffer.indexOf(10);if(newline<0)return;
  const line=buffer.subarray(0,newline),rest=buffer.subarray(newline+1);if(rest.length){reject(null,'pipelined-input');return;}buffer=Buffer.alloc(0);
  let request;
  try{const text=line.toString('utf8');if(!Buffer.from(text).equals(line))throw Error();request=JSON.parse(text);
   if(!request||Array.isArray(request)||Object.keys(request).sort().join(',')!=='id,method'||!Number.isSafeInteger(request.id)||request.id<=lastId||!['start','poll','status','frame','close'].includes(request.method))throw Error();
  }catch(_){reject(null,'invalid-request');return;}
  lastId=request.id;++accepted;
  if(request.method==='close'){void stop(request.id,null);return;}
  if(busy){if(queued){reject(request.id,'queue-bound');return;}queued=request;return;}task=dispatch(request);
 }
 input.on('data',onData);input.once('end',()=>{void stop(null,'input-ended');});input.once('error',()=>{void stop(null,'input-error');});output.once('error',()=>{void stop(null,'output-error');});
 return {done};
}
module.exports={servePreview};
