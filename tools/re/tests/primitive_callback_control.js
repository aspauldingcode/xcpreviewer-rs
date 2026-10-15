'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),{EventEmitter}=require('node:events');
const e=path.resolve(process.argv[2]),phase=process.argv[3],prod=path.resolve(process.argv[4]);
const reasons=()=>{const readonly=Error('owned readonly');Object.defineProperty(readonly,'record',{value:'owned',writable:false,configurable:false});return [['string','owned primitive'],['zero',0],['false',false],['null',null],['undefined',undefined],['empty',''],['bigint',17n],['symbol',Symbol('owned')],['opaque',Object.create(null)],['error',Error('owned error')],['frozen',Object.freeze(Error('owned frozen'))],['readonly',readonly]];};
(async()=>{const results=[];
 for(const [name,reason] of reasons()){
  const child=new EventEmitter();child.pid=900001;child.exitCode=null;child.signalCode=null;const writes=[],kills=[];
  child.stdio=Array.from({length:4},()=>new EventEmitter());[child.stdin,child.stdout,child.stderr]=child.stdio;for(const stream of child.stdio)stream.destroy=()=>{};child.stdin.write=value=>{writes.push(value);return true;};
  const sandbox={module:{exports:{}},Buffer,Error,setTimeout,clearTimeout,__dirname:path.dirname(prod),process:{platform:'darwin',kill:(pid,signal)=>kills.push({pid,signal})},require:n=>n==='node:child_process'?{spawn:()=>child}:require(n)};
  vm.runInNewContext(fs.readFileSync(path.join(e,phase+'.js'),'utf8'),sandbox,{filename:prod});
  const helper=path.join(e,'unused-helper');const job=sandbox.module.exports.runObserved('never-launched',[],{observer:{helper,sha256:crypto.createHash('sha256').update(fs.readFileSync(helper)).digest('hex')},timeout:50,onObservation:()=>{throw reason;}});
  let settled=false,error,record;job.then(r=>{settled=true;record=r;},x=>{settled=true;error=x;record=x.record;});
  child.stdio[3].emit('data',Buffer.from(JSON.stringify({kind:'observed',rows:[]})+'\n'));
  const complete={kind:'complete',drained:true,target_code:43,failure:'abort',observations:1,tracked:0,remaining_observed:0,scope:'Injected source control, no native process'};
  child.stdio[3].emit('data',Buffer.from(JSON.stringify(complete)+'\n'));child.signalCode='SIGKILL';let closeThrow=null;
  try{child.emit('close',null,'SIGKILL');}catch(x){closeThrow={name:x.name,message:x.message};}
  await new Promise(resolve=>setTimeout(resolve,5));
  results.push({name,settled,closeThrow,error:error?{name:error.name,message:error.message,originalIdentity:error===reason}:null,record:record||null,writes,kills});
 }
 fs.writeFileSync(path.join(e,phase+'-results.json'),JSON.stringify(results,null,2)+'\n');
})().catch(error=>{console.error(error);process.exitCode=1;});
