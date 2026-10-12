// Actual builder JS/filesystem stage budget with synthetic failed execution boundary.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),Module=require('node:module');
const e=path.resolve(process.argv[2]),production=path.resolve(process.argv[3]),cfg=JSON.parse(fs.readFileSync(path.join(e,'config.json'))),source=fs.readFileSync(path.join(e,'source.swift')),sentinel=Buffer.from([0,1,2,255,10,42]);let calls=0;
const fake=async()=>{const id=++calls,error=Error('Owned stage handoff '+id);error.record={syntheticJobId:id,scope:'Synthetic execution boundary'};throw error;};
function implementation(phase){const m=new Module(production,module);m.filename=production;m.paths=Module._nodeModulePaths(path.dirname(production));const original=m.require.bind(m);m.require=id=>id==='./observed_compiler.js'?{runObserved:fake}:original(id);m._compile(fs.readFileSync(path.join(e,'rust-builder-'+phase+'.js'),'utf8'),production);return m.exports.rustSourceBuilder;}
(async()=>{
 const results=[];
 for(const phase of ['before','after']){
  calls=0;const root=path.join(e,phase);fs.mkdirSync(root);fs.writeFileSync(path.join(root,'unrelated.sentinel'),sentinel);
  const builder=implementation(phase)({...cfg,root,stageLimit:2,historyLimit:1,oracle:()=>{throw Error('No oracle call');}}),cancelled=new AbortController();cancelled.abort();let preError=null;
  try{await builder(source,{signal:cancelled.signal});}catch(error){preError=String(error);}assert.equal(preError,'Error: Rust build aborted before staging');assert.equal(fs.readdirSync(root).length,1);assert.equal(calls,0);const preBudget=builder.budget?builder.budget():null,errors=[];
  for(let id=1;id<=3;id++){try{await builder(source,{signal:new AbortController().signal});}catch(error){errors.push(String(error));}}
  const stages=fs.readdirSync(root).filter(name=>name.startsWith('build-'));assert.equal(stages.length,phase==='before'?3:2);assert.equal(calls,stages.length);assert.deepEqual(fs.readFileSync(path.join(root,'unrelated.sentinel')),sentinel);
  const stagesBeforeRetry=stages.slice();let retryError=null;const beforeCalls=calls;
  if(phase==='after'){try{await builder(source,{signal:new AbortController().signal});}catch(error){retryError=String(error);}assert.equal(retryError,'Error: Rust build stage budget exhausted');assert.equal(calls,beforeCalls);assert.deepEqual(fs.readdirSync(root).filter(name=>name.startsWith('build-')),stagesBeforeRetry);}
  const files=stages.map(stage=>{assert.deepEqual(fs.readFileSync(path.join(root,stage,'source.swift')),source);return {stage,failure:JSON.parse(fs.readFileSync(path.join(root,stage,'failure.json')))};});
  results.push({phase,preError,preBudget,errors,stageCount:stages.length,syntheticHandoffs:calls,budget:builder.budget?builder.budget():null,history:builder.history(),records:builder.records(),failures:builder.failures(),files,retryError,sentinelPreserved:true});
 }
 const invalid=[];for(const value of [0,257,-1,1.5,true,'2']){const root=path.join(e,'invalid-'+invalid.length);let error=null;try{implementation('after')({...cfg,root,stageLimit:value,oracle:()=>Buffer.alloc(16384)});}catch(e){error=String(e);}assert(error&&!fs.existsSync(root));invalid.push({value,rejected:true,rootCreated:false});}
 fs.writeFileSync(path.join(e,'result.json'),JSON.stringify({results,invalid,actualCompilerJobs:0,scope:'Per-builder allocation count; synthetic execution boundary; no disk-byte or cross-instance quota'},null,2)+'\n');console.log(JSON.stringify(results.map(r=>({phase:r.phase,stages:r.stageCount,calls:r.syntheticHandoffs,budget:r.budget,retry:r.retryError}))));
})().catch(error=>{console.error(error);process.exitCode=1;});
