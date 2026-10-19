// Calls the exact installed provider helper. Only adds listeners to owned child handles.
import fs from 'node:fs';
import crypto from 'node:crypto';
import cp from 'node:child_process';
import {syncBuiltinESMExports} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('.',import.meta.url)),plan=JSON.parse(fs.readFileSync(root+'plan.json'));
const need=(v,s)=>{if(!v)throw Error(s)};
need(crypto.createHash('sha256').update(fs.readFileSync(plan.library_path)).digest('hex')===plan.library_sha256,'shipped source drift');
const {execFileOutput}=await import(pathToFileURL(plan.library_path).href);
const original=cp.execFile;let current;
const now=()=>Number(process.hrtime.bigint())/1e6;
const hard=setTimeout(()=>process.exit(86),7000);
cp.execFile=function(command,args,options,callback){
 need(command===plan.node_path&&args[0]===root+'child.mjs'&&current&&!current.child,'only owned spawn');
 const child=original.call(this,command,args,options,callback);current.child=child;current.pid=child.pid;
 current.close=new Promise(resolve=>child.once('close',(code,signal)=>{current.close_at=now();current.close_code=code;current.close_signal=signal;resolve()}));
 const state=current;child.once('exit',(code,signal)=>{state.exit_at=now();state.exit_code=code;state.exit_signal=signal});
 return child;
};syncBuiltinESMExports();
const rows=[];
try{
 for(const mode of ['default','stoppable']){
  const folder=root+'owned-documents/'+mode;fs.mkdirSync(folder);const nonce=crypto.randomBytes(16).toString('hex');
  const row={mode,nonce,folder:mode};current=row;const abort=new AbortController();
  const pending=execFileOutput(plan.node_path,[root+'child.mjs',folder,nonce],{signal:abort.signal,timeout:1200,maxBuffer:16384,...(mode==='stoppable'?{stopSignal:'SIGTERM'}:{})}).then(
   value=>{row.unexpected_success=true;row.stdout=value.stdout},
   error=>{row.error_name=error.name;row.error_code=error.code;row.stdout=error.stdout;row.stderr=error.stderr}
  ).then(()=>{row.settled_at=now();row.marker_present_at_settlement=fs.existsSync(folder+'/marker.raw');row.exit_code_at_settlement=row.child.exitCode;row.signal_code_at_settlement=row.child.signalCode;row.exit_seen_at_settlement=typeof row.exit_at==='number';row.close_seen_at_settlement=typeof row.close_at==='number'});
  const until=now()+2000;
  while(!fs.existsSync(folder+'/ready.json')){need(now()<until,'owned readiness');await new Promise(resolve=>setTimeout(resolve,2))}
  const ready=JSON.parse(fs.readFileSync(folder+'/ready.json'));need(ready.pid===row.pid&&ready.ppid===process.pid&&ready.nonce===nonce,'owned identity');
  row.abort_at=now();abort.abort('owned test');await pending;await row.close;
  need(row.exit_code===0&&row.close_code===0&&row.exit_signal===null&&row.close_signal===null,'actual owned exit');
  const marker=fs.readFileSync(folder+'/marker.raw');row.marker_sha256=crypto.createHash('sha256').update(marker).digest('hex');row.marker_bytes=marker.length;
  const term=JSON.parse(fs.readFileSync(folder+'/term.json')),done=JSON.parse(fs.readFileSync(folder+'/done.json'));
  need(term.pid===row.pid&&done.pid===row.pid&&term.nonce===nonce&&done.nonce===nonce&&term.signal==='SIGTERM'&&done.intended_exit===0,'owned handler receipts');
  delete row.child;delete row.close;rows.push(row);
 }
}finally{cp.execFile=original;syncBuiltinESMExports();clearTimeout(hard)}
console.log(JSON.stringify({pid:process.pid,environment:{node:process.version,v8:process.versions.v8,arch:process.arch,platform:process.platform},library_sha256:plan.library_sha256,instrumentation:'execFile wrapper returns original child unchanged; owned exit/close listeners only',rows,native_UI_execution:false,provider_target_UI_settlement_qualified:false,product_integration:false}));
