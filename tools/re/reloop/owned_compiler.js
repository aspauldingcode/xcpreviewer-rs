'use strict';
// Trusted owned POSIX compiler trees only. Never attach to existing processes.
const {spawn}=require('node:child_process'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function runOwned(command,args,{signal,timeout=5000,limit=65536,supervisorPython='python3'}={}){
 assert(process.platform!=='win32','POSIX owned process groups required');assert(Number.isSafeInteger(timeout)&&timeout>=50&&timeout<=30000);assert(Number.isSafeInteger(limit)&&limit>=1&&limit<=1048576);
 return new Promise((resolve,reject)=>{
  if(signal?.aborted){reject(Error('Owned compiler aborted before spawn'));return;}
  const child=spawn(supervisorPython,[path.join(__dirname,'owned_group_anchor.py'),command,...args],{detached:true,stdio:['ignore','pipe','pipe','pipe']});
  let stdout=Buffer.alloc(0),stderr=Buffer.alloc(0),control='',failure=null,targetCode=null,reported=false;
  const stop=reason=>{if(reason)failure ||= reason;if(child.pid&&child.exitCode===null&&child.signalCode===null){try{process.kill(-child.pid,'SIGKILL');}catch(e){if(e.code!=='ESRCH')failure=e;}}};
  const abort=()=>stop(Error('Owned compiler aborted'));signal?.addEventListener('abort',abort,{once:true});
  const timer=setTimeout(()=>stop(Error('Owned compiler deadline exceeded')),timeout);
  const collect=(kind,b)=>{if(stdout.length+stderr.length+b.length>limit){stop(Error('Owned compiler output limit'));return;}if(kind==='stdout')stdout=Buffer.concat([stdout,b]);else stderr=Buffer.concat([stderr,b]);};
  child.stdout.on('data',b=>collect('stdout',b));child.stderr.on('data',b=>collect('stderr',b));child.on('error',e=>{failure=e;});
  child.stdio[3].on('data',b=>{
   if(reported){stop(Error('Duplicate owned anchor report'));return;}control+=b.toString();
   if(control.length>4096){stop(Error('Owned anchor report limit'));return;}
   if(!control.endsWith('\n'))return;
   try{const report=JSON.parse(control);assert(Number.isSafeInteger(report.target_code));targetCode=report.target_code;reported=true;stop(targetCode===0?null:Error('Owned compiler exited '+targetCode));}
   catch(e){stop(e);}
  });
  child.on('close',(anchorCode,term)=>{clearTimeout(timer);signal?.removeEventListener('abort',abort);
   const record={pid:child.pid,code:targetCode,anchorCode,signal:term,anchorReported:reported,stdout:stdout.toString(),stderr:stderr.toString()};
   if(failure||!reported||targetCode!==0||term!=='SIGKILL'){const error=failure||Error('Owned anchor did not complete verified drain');error.record=record;reject(error);}else resolve(record);
  });
 });
}
function compiler(options){
 const {python,cli,clang,wasmLd,node,root,oracle,stride=64}=options;assert.equal(typeof oracle,'function');fs.mkdirSync(root,{recursive:true});
 const execute=options.observer?require('./observed_compiler.js').runObserved:runOwned;
 const records=[];
 const build=async(source,{signal})=>{
  const stage=fs.mkdtempSync(path.join(root,'build-'));const sourcePath=path.join(stage,'source.swift');fs.writeFileSync(sourcePath,source);
  let execution;
  try{execution=await execute(python,[cli,sourcePath,'--cache',path.join(root,'cache'),'--output',path.join(stage,'published'),'--clang',clang,'--wasm-ld',wasmLd,'--node',node,'--stride',String(stride)],{signal,timeout:5000,supervisorPython:python,observer:options.observer});}
  catch(e){fs.writeFileSync(path.join(stage,'failure.json'),JSON.stringify({error:String(e),record:e.record},null,2));throw e;}
  const receipt=JSON.parse(execution.stdout);assert(receipt.ok);assert(/^[a-f0-9]{64}$/.test(receipt.entry_sha256));assert.equal(receipt.source_sha256,sha(source));
  const folder=path.join(stage,'published/versions',receipt.entry_sha256),rawManifest=fs.readFileSync(path.join(folder,'manifest.json'));assert.equal(sha(rawManifest),receipt.entry_sha256);
  const manifest=JSON.parse(rawManifest);for(const [name,row] of Object.entries(manifest.files)){assert(!name.includes('/')&&!name.includes('..'));const p=path.join(folder,name);assert(!fs.lstatSync(p).isSymbolicLink());const b=fs.readFileSync(p);assert.equal(b.length,row.bytes);assert.equal(sha(b),row.sha256);}
  const module=fs.readFileSync(path.join(folder,'view.wasm'));assert.equal(sha(module),receipt.module_sha256);assert(module.length<=1048576);
  const expected=oracle(source);assert(Buffer.isBuffer(expected)&&expected.length===16384);assert.deepEqual(fs.readFileSync(path.join(folder,'allocation.raw')),expected);
  const record={sourceSha256:receipt.source_sha256,moduleSha256:receipt.module_sha256,cacheHit:receipt.cache_hit,stage:path.basename(stage),allocationBytes:16384};records.push(record);
  fs.writeFileSync(path.join(stage,'execution.json'),JSON.stringify(execution,null,2));
  return {build:{module,moduleSha256:receipt.module_sha256,sourceSha256:receipt.source_sha256,config:receipt.config,stride:receipt.stride},expected};
 };
 build.records=()=>records.map(r=>({...r}));return build;
}
module.exports={runOwned,compiler};
