'use strict';
// Local custom NDJSON process wrapper; no JSON-RPC/MCP compatibility claim.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawnSync}=require('node:child_process');
const {readArtifact}=require('./reloop/bounded_artifact.js'),{rustSourceBuilder}=require('./reloop/rust_source_builder.js'),{PreviewSession}=require('./reloop/preview_session.js'),{servePreview}=require('./reloop/preview_channel.js');
(async()=>{
 const [configPath,source,root,durationText='10000']=process.argv.slice(2);assert(process.argv.length>=5&&process.argv.length<=6);assert([configPath,source,root].every(path.isAbsolute));
 const raw=readArtifact(configPath);assert(raw.length<=16384);const cfg=JSON.parse(raw);assert(cfg&&typeof cfg==='object'&&!Array.isArray(cfg));
 assert(Object.keys(cfg).sort().join(',')==='cli,observer,python,rustc,rustcSha,toolchainPin');
 const deadline=Number(durationText);assert(Number.isSafeInteger(deadline)&&deadline>=500&&deadline<=10000);fs.mkdirSync(root);
 const oracle=bytes=>{
  const r=spawnSync(cfg.python,[path.join(__dirname,'primary_oracle_cli.py')],{input:bytes,timeout:2000,maxBuffer:32768,killSignal:'SIGTERM'});
  assert(!r.error&&r.status===0&&r.stdout.length===16384,'Finite oracle failed');return r.stdout;
 };
 const builder=rustSourceBuilder({...cfg,root,oracle}),session=new PreviewSession(source,builder),channel=servePreview(process.stdin,process.stdout,session,{deadline});
 const result=await channel.done;
 fs.writeFileSync(path.join(root,'session-lifecycle.json'),JSON.stringify({channel:result,final:session.status(),builds:builder.records(),failures:builder.failures()},null,2)+'\n');
 process.stderr.write(JSON.stringify({kind:'closed',channel:result,lifecycle:session.status().lifecycle})+'\n');
})().catch(()=>{process.stderr.write('{"kind":"startup-failed"}\n');process.exitCode=2;});
