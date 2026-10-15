'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),{EventEmitter}=require('node:events');
const e=path.resolve(process.argv[2]),phase=process.argv[3],prod=path.resolve(process.argv[4]);
(async()=>{const results=[];
 for(const mode of ['resolved','rejected','pending','thenable','getter','plain']){
  let thenCalls=0,getterCalls=0;const unhandled=[];const listen=error=>unhandled.push({name:error.name,message:error.message});process.on('unhandledRejection',listen);
  const child=new EventEmitter();child.pid=900001;child.exitCode=null;child.signalCode=null;const writes=[],kills=[];
  child.stdio=Array.from({length:4},()=>new EventEmitter());[child.stdin,child.stdout,child.stderr]=child.stdio;for(const stream of child.stdio)stream.destroy=()=>{};child.stdin.write=value=>{writes.push(value);return true;};
  const sandbox={module:{exports:{}},Buffer,Error,setTimeout,clearTimeout,__dirname:path.dirname(prod),process:{platform:'darwin',kill:(pid,signal)=>kills.push({pid,signal})},require:n=>n==='node:child_process'?{spawn:()=>child}:require(n)};
  vm.runInNewContext(fs.readFileSync(path.join(e,phase+'.js'),'utf8'),sandbox,{filename:prod});
  const helper=path.join(e,'unused-helper');let error,record;
  const job=sandbox.module.exports.runObserved('never-launched',[],{observer:{helper,sha256:crypto.createHash('sha256').update(fs.readFileSync(helper)).digest('hex')},timeout:50,onObservation:()=>{
   if(mode==='resolved')return Promise.resolve();
   if(mode==='rejected')return Promise.reject(Error('Owned async rejection'));
   if(mode==='pending')return new Promise(()=>{});
   if(mode==='thenable')return {then:(_resolve,reject)=>{thenCalls++;reject(Error('Owned thenable rejection'));}};
   if(mode==='getter')return {get then(){getterCalls++;throw Error('Owned then getter');}};
   return 42;
  }});
  child.stdio[3].emit('data',Buffer.from(JSON.stringify({kind:'observed',rows:[]})+'\n'));
  const cancelled=writes.length!==0;
  child.stdio[3].emit('data',Buffer.from(JSON.stringify({kind:'complete',drained:true,target_code:cancelled?43:0,failure:cancelled?'abort':null,observations:1,tracked:0,remaining_observed:0,scope:'Injected source control, no native process'})+'\n'));
  child.signalCode='SIGKILL';child.emit('close',null,'SIGKILL');try{record=await job;}catch(x){error=x;record=x.record;}
  await new Promise(resolve=>setTimeout(resolve,15));process.off('unhandledRejection',listen);
  results.push({mode,error:error?{name:error.name,message:error.message}:null,record,writes,kills,unhandled,thenCalls,getterCalls});
 }
 fs.writeFileSync(path.join(e,phase+'-results.json'),JSON.stringify(results,null,2)+'\n');
})().catch(error=>{console.error(error);process.exitCode=1;});
