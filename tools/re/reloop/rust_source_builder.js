// Reusable finite-expression Rust builder. Owned observed compilation only.
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {runObserved}=require('./observed_compiler.js');const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function rustSourceBuilder(cfg){
 assert.equal(typeof cfg.oracle,'function');assert(/^[a-f0-9]{64}$/.test(cfg.toolchainPin));assert(/^[a-f0-9]{64}$/.test(cfg.rustcSha));assert(path.isAbsolute(cfg.root));fs.mkdirSync(cfg.root,{recursive:true});
 const timeout=cfg.timeout??5000;assert(Number.isSafeInteger(timeout)&&timeout>=50&&timeout<=5000,'Bounded Rust build deadline required');
 const records=[],failures=[];
 const build=async(source,{signal})=>{
  assert(Buffer.isBuffer(source)&&source.length>0&&source.length<=4096);const stage=fs.mkdtempSync(path.join(cfg.root,'build-')),file=path.join(stage,'source.swift');fs.writeFileSync(file,source);
  let execution;
  try{execution=await runObserved(cfg.python,[cfg.cli,file,'--output',path.join(stage,'result'),'--rustc',cfg.rustc,'--rustc-sha256',cfg.rustcSha,'--toolchain-pin',cfg.toolchainPin],{signal,timeout,observer:cfg.observer,supervisorPython:cfg.python,onObservation:cfg.onObservation});
  const receipt=JSON.parse(execution.stdout);assert.equal(receipt.source_sha256,sha(source));assert.equal(receipt.rustc_sha256,cfg.rustcSha);assert.equal(receipt.toolchain_sha256,cfg.toolchainPin);
  const target=path.join(stage,'result/view.wasm'),info=fs.lstatSync(target);assert(info.isFile()&&!info.isSymbolicLink()&&info.size<=1048576);const module=fs.readFileSync(target);assert.equal(receipt.module_sha256,sha(module));
  assert(execution.report.drained&&execution.report.remaining_observed===0&&execution.report.target_code===0);
  const expected=cfg.oracle(source);assert(Buffer.isBuffer(expected)&&expected.length===16384);records.push({receipt,execution,stage:path.basename(stage)});
  return {build:{module,moduleSha256:receipt.module_sha256,sourceSha256:receipt.source_sha256,config:receipt.config,stride:cfg.stride??64},expected};
  }catch(e){const failure={error:String(e),record:e.record||execution};failures.push(failure);fs.writeFileSync(path.join(stage,'failure.json'),JSON.stringify(failure));throw e;}
 };
 build.records=()=>JSON.parse(JSON.stringify(records));build.failures=()=>JSON.parse(JSON.stringify(failures));return build;
}
module.exports={rustSourceBuilder};
