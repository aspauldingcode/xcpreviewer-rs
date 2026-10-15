'use strict';
// Explicit macOS public observer dependency. Default inherited-group path stays available.
const {TextDecoder}=require('node:util');
const {spawn}=require('node:child_process'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
function validateComplete(row){
 assert(row&&typeof row==='object'&&!Array.isArray(row));assert.equal(row.kind,'complete');
 assert.equal(typeof row.drained,'boolean');assert(row.target_code===null||Number.isSafeInteger(row.target_code));
 if(row.drained){
  assert.deepEqual(Object.keys(row).sort(),['drained','failure','kind','observations','remaining_observed','scope','target_code','tracked'].sort());
  assert(row.failure===null||typeof row.failure==='string');assert(Number.isSafeInteger(row.target_code));
  assert(Number.isSafeInteger(row.tracked)&&row.tracked>=0&&row.tracked<=256);
  assert(Number.isSafeInteger(row.observations)&&row.observations>=1);
  assert.equal(row.remaining_observed,0);assert.equal(typeof row.scope,'string');assert(row.scope.length>0&&row.scope.length<=1024);
 }else{
  assert.deepEqual(Object.keys(row).sort(),['drained','failure','kind','target_code'].sort());
  assert.equal(typeof row.failure,'string');assert(row.failure.length>0);
 }
 return row;
}
function runObserved(command,args,{observer,supervisorPython='python3',signal,timeout=5000,limit=65536,onObservation=()=>{}}={}){
 assert.equal(process.platform,'darwin');assert(observer&&path.isAbsolute(observer.helper)&&/^[a-f0-9]{64}$/.test(observer.sha256));
 assert(Number.isSafeInteger(timeout)&&timeout>=50&&timeout<=30000);assert(Number.isSafeInteger(limit)&&limit>=1&&limit<=1048576);assert.equal(typeof onObservation,'function');
 assert(!fs.lstatSync(observer.helper).isSymbolicLink());assert.equal(crypto.createHash('sha256').update(fs.readFileSync(observer.helper)).digest('hex'),observer.sha256);
 return new Promise((resolve,reject)=>{
  if(signal?.aborted){reject(Error('Observed compiler aborted before spawn'));return;}
  const child=spawn(supervisorPython,[path.join(__dirname,'observed_group_anchor.py'),observer.helper,observer.sha256,String(timeout),command,...args],{detached:true,stdio:['pipe','pipe','pipe','pipe']});
  const decoder=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true});
  let failure=null,report=null,control='',controlBytes=0,stdout=Buffer.alloc(0),stderr=Buffer.alloc(0),requested=false,emergencyClosed=false;
  const kill=()=>{if(child.pid&&child.exitCode===null&&child.signalCode===null){try{process.kill(-child.pid,'SIGKILL');}catch(e){if(e.code!=='ESRCH')failure ||= e;}}};
  const normalize=reason=>{try{return reason instanceof Error?reason:Error(String(reason));}catch(_){return Error('Observed non-Error failure');}};
  const cancel=reason=>{failure ||= normalize(reason);if(!requested){requested=true;child.stdin.write('abort\n');}};
  const abort=()=>cancel(Error('Observed compiler aborted'));signal?.addEventListener('abort',abort,{once:true});
  const timer=setTimeout(()=>{emergencyClosed=true;failure ||= Error('Observed supervisor hard deadline; cleanup unverified');kill();for(const stream of [child.stdin,child.stdout,child.stderr,child.stdio[3]])stream.destroy();},timeout+5000);
  const collect=(kind,b)=>{if(stdout.length+stderr.length+b.length>limit){cancel(Error('Observed compiler output limit'));return;}if(kind==='stdout')stdout=Buffer.concat([stdout,b]);else stderr=Buffer.concat([stderr,b]);};
  child.stdout.on('data',b=>collect('stdout',b));child.stderr.on('data',b=>collect('stderr',b));
  for(const stream of [child.stdin,child.stdout,child.stderr,child.stdio[3]])stream.on('error',e=>{failure ||= e;});
  child.on('error',e=>{failure ||= e;});
  child.stdio[3].on('data',b=>{
   controlBytes+=b.length;if(controlBytes>65536){cancel(Error('Observed report limit'));return;}
   try{control+=decoder.decode(b,{stream:true});}catch(e){cancel(e);return;}
   while(control.includes('\n')){
    const end=control.indexOf('\n'),line=control.slice(0,end);control=control.slice(end+1);
    try{
     const row=JSON.parse(line);assert(!report);
     if(row.kind==='observed'){assert(Array.isArray(row.rows));try{onObservation(row.rows);}catch(e){cancel(e);}}
     else{report=validateComplete(row);if(row.drained!==true||row.remaining_observed!==0||!Number.isSafeInteger(row.target_code)||row.failure||row.target_code!==0)failure ||= Error('Observed compiler failed: '+String(row.failure||row.target_code));kill();}
    }catch(e){cancel(e);}
   }
  });
  child.on('close',(code,term)=>{try{control+=decoder.decode();}catch(e){failure ||= e;}if(control.length)failure ||= Error('Observed report truncated trailing data');clearTimeout(timer);signal?.removeEventListener('abort',abort);
   const record={pid:child.pid,anchorCode:code,signal:term,report,emergencyClosed,privateAbortRequested:requested,stdout:stdout.toString(),stderr:stderr.toString(),stdoutBytes:stdout.length,stderrBytes:stderr.length,stdoutSha256:crypto.createHash('sha256').update(stdout).digest('hex'),stderrSha256:crypto.createHash('sha256').update(stderr).digest('hex')};
   if(failure||report?.drained!==true||report.remaining_observed!==0||report.target_code!==0||term!=='SIGKILL'){
    let e=normalize(failure||Error('Observed cleanup unverified'));
    try{Object.defineProperty(e,'record',{value:record,enumerable:true,configurable:true,writable:true});}
    catch(_){let message;try{message=e.message;}catch(_){message='Observed failure record unavailable';}e=Error(typeof message==='string'?message:'Observed failure record unavailable');e.record=record;}
    reject(e);
   }else resolve(record);
  });
 });
}
module.exports={runObserved,validateComplete};
