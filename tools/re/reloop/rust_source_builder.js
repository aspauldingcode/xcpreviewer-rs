// Reusable finite-expression Rust builder. Owned observed compilation only.
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {readArtifact}=require('./bounded_artifact.js');
const {validateRustReceipt}=require('./rust_receipt.js');
const {runObserved}=require('./observed_compiler.js');const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function rustSourceBuilder(cfg){
 assert.equal(typeof cfg.oracle,'function');assert(/^[a-f0-9]{64}$/.test(cfg.toolchainPin));assert(/^[a-f0-9]{64}$/.test(cfg.rustcSha));assert(path.isAbsolute(cfg.root));
 const historyLimit=cfg.historyLimit??64;assert(Number.isSafeInteger(historyLimit)&&historyLimit>=1&&historyLimit<=256,'Bounded build history limit required');
 const stageLimit=cfg.stageLimit??64;assert(Number.isSafeInteger(stageLimit)&&stageLimit>=1&&stageLimit<=256,'Bounded build stage limit required');
 fs.mkdirSync(cfg.root,{recursive:true});
 const timeout=cfg.timeout??5000;assert(Number.isSafeInteger(timeout)&&timeout>=50&&timeout<=5000,'Bounded Rust build deadline required');
 const records=[],failures=[];let recordsDropped=0,failuresDropped=0,stagesCreated=0;
 const retain=(list,value,kind)=>{if(list.length===historyLimit){list.shift();if(kind==='record')recordsDropped=Math.min(Number.MAX_SAFE_INTEGER,recordsDropped+1);else failuresDropped=Math.min(Number.MAX_SAFE_INTEGER,failuresDropped+1);}list.push(value);};
 const build=async(source,{signal})=>{
  assert(Buffer.isBuffer(source)&&source.length>0&&source.length<=4096);
  if(signal?.aborted)throw Error('Rust build aborted before staging');
  if(stagesCreated>=stageLimit)throw Error('Rust build stage budget exhausted');
  const stage=fs.mkdtempSync(path.join(cfg.root,'build-')),file=path.join(stage,'source.swift');++stagesCreated;fs.writeFileSync(file,source);
  let execution;
  try{execution=await runObserved(cfg.python,[cfg.cli,file,'--output',path.join(stage,'result'),'--rustc',cfg.rustc,'--rustc-sha256',cfg.rustcSha,'--toolchain-pin',cfg.toolchainPin],{signal,timeout,observer:cfg.observer,supervisorPython:cfg.python,onObservation:cfg.onObservation});
  assert(Buffer.byteLength(execution.stdout)<=16384,'Rust receipt size limit');const receipt=JSON.parse(execution.stdout);
  const target=path.join(stage,'result/view.wasm'),module=readArtifact(target),kernel=path.join(__dirname,'../rust/canvas-core/src'),sources={};
  for(const name of ['contract.rs','wasm-template.rs'])sources[name]=sha(readArtifact(path.join(kernel,name)));
  validateRustReceipt(receipt,{source_sha256:sha(source),module_sha256:sha(module),rustc_sha256:cfg.rustcSha,toolchain_sha256:cfg.toolchainPin,generated_sha256:sha(readArtifact(path.join(stage,'result/module.rs'))),sources});
  assert(execution.report.drained&&execution.report.remaining_observed===0&&execution.report.target_code===0);
  const expected=cfg.oracle(source);assert(Buffer.isBuffer(expected)&&expected.length===16384);retain(records,{receipt,execution,stage:path.basename(stage)},'record');
  return {build:{module,moduleSha256:receipt.module_sha256,sourceSha256:receipt.source_sha256,config:receipt.config,stride:cfg.stride??64},expected};
  }catch(e){const failure={error:String(e),record:e.record||execution};retain(failures,failure,'failure');fs.writeFileSync(path.join(stage,'failure.json'),JSON.stringify(failure));throw e;}
 };
 build.budget=()=>({stageLimit,stagesCreated});
 build.history=()=>({limit:historyLimit,recordsDropped,failuresDropped});
 build.records=()=>JSON.parse(JSON.stringify(records));build.failures=()=>JSON.parse(JSON.stringify(failures));return build;
}
module.exports={rustSourceBuilder};
