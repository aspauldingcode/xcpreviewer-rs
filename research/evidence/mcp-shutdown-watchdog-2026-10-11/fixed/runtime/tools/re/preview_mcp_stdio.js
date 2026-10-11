'use strict';
// Owned bounded MCP stdio prototype; independent client subset, no SDK conformance claim.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawnSync}=require('node:child_process');
const {readArtifact}=require('./reloop/bounded_artifact.js'),{rustSourceBuilder}=require('./reloop/rust_source_builder.js'),{PreviewSession}=require('./reloop/preview_session.js'),{PreviewMcp}=require('./reloop/preview_mcp.js'),{serveMcp}=require('./reloop/mcp_channel.js');
(async()=>{
 const [configPath,source,root,durationText='10000']=process.argv.slice(2);assert(process.argv.length>=5&&process.argv.length<=6);assert([configPath,source,root].every(path.isAbsolute));
 const raw=readArtifact(configPath);assert(raw.length<=16384);const cfg=JSON.parse(raw);assert(cfg&&typeof cfg==='object'&&!Array.isArray(cfg));
 assert(Object.keys(cfg).sort().join(',')==='cli,observer,python,rustc,rustcSha,toolchainPin');
 const deadline=Number(durationText);assert(Number.isSafeInteger(deadline)&&deadline>=500&&deadline<=10000);fs.mkdirSync(root);
 const oracle=bytes=>{
  const r=spawnSync(cfg.python,[path.join(__dirname,'primary_oracle_cli.py')],{input:bytes,timeout:2000,maxBuffer:32768,killSignal:'SIGTERM'});
  assert(!r.error&&r.status===0&&r.stdout.length===16384,'Finite oracle failed');return r.stdout;
 };
 const builder=rustSourceBuilder({...cfg,root,oracle}),session=new PreviewSession(source,builder),channel=serveMcp(process.stdin,process.stdout,new PreviewMcp(session),session,{deadline});
 // Bound asynchronous shutdown even if a trusted close adapter never settles.
 const watchdog=setTimeout(()=>{
  const snapshot={kind:'shutdown-timeout',deadlineMs:deadline,graceMs:1000,cleanup:'unknown',final:session.status()};
  try{fs.writeFileSync(path.join(root,'shutdown-timeout.json'),JSON.stringify(snapshot,null,2)+'\n');}catch(_){}
  try{fs.writeSync(2,JSON.stringify(snapshot)+'\n');}catch(_){}
  process.exit(4);
 },deadline+1000);
 let result;
 try{result=await channel.done;}finally{clearTimeout(watchdog);}
 fs.writeFileSync(path.join(root,'session-lifecycle.json'),JSON.stringify({channel:result,final:session.status(),builds:builder.records(),failures:builder.failures()},null,2)+'\n');
 const cleanupFailed=result.cleanup!=='complete';
 process.stderr.write(JSON.stringify({kind:cleanupFailed?'cleanup-failed':'closed',channel:result,lifecycle:session.status().lifecycle})+'\n');
 if(cleanupFailed)process.exitCode=3;
})().catch(()=>{process.stderr.write('{"kind":"startup-failed"}\n');process.exitCode=2;});
