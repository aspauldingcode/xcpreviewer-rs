// Builder receipt/history workload with synthetic execution boundary; no compiler spawn.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),Module=require('node:module');
const e=path.resolve(process.argv[2]),production=path.resolve(process.argv[3]),rawRoot=path.resolve(process.argv[4]),cfg=JSON.parse(fs.readFileSync(path.join(e,'config.json'))),fixture=path.join(e,'fixture'),source=fs.readFileSync(path.join(fixture,'source.swift')),receipt=JSON.parse(fs.readFileSync(path.join(fixture,'receipt.json'))),expected=fs.readFileSync(path.join(fixture,'expected.raw'));let currentId=0;
fs.mkdirSync(rawRoot,{recursive:true});fs.mkdirSync(path.join(e,'retained-failures'));const results=[];
const fake=async(_command,args)=>{
 const id=currentId;if(id%2===0){const error=Error('Owned history failure '+id);error.record={syntheticJobId:id,scope:'Synthetic execution boundary'};throw error;}
 const out=args[args.indexOf('--output')+1];fs.mkdirSync(out);for(const name of ['module.rs','view.wasm'])fs.copyFileSync(path.join(fixture,name),path.join(out,name));
 return {syntheticJobId:id,stdout:JSON.stringify(receipt),stderr:'',report:{drained:true,remaining_observed:0,target_code:0,scope:'Synthetic execution boundary'}};
};
function implementation(phase){const m=new Module(production,module);m.filename=production;m.paths=Module._nodeModulePaths(path.dirname(production));const original=m.require.bind(m);m.require=id=>id==='./observed_compiler.js'?{runObserved:fake}:original(id);m._compile(fs.readFileSync(path.join(e,'rust-builder-'+phase+'.js'),'utf8'),production);return m.exports.rustSourceBuilder;}
(async()=>{
 for(const phase of ['before','after'])for(const [name,limit,n] of [['default',64,130],['configured',4,10]]){
  const root=path.join(rawRoot,phase+'-'+name),options={...cfg,root,oracle:()=>expected};if(name==='configured')options.historyLimit=limit;const builder=implementation(phase)(options);
  for(let id=1;id<=n;id++){currentId=id;try{await builder(source,{signal:new AbortController().signal});assert(id%2===1);}catch(error){assert(id%2===0);assert.equal(String(error),'Error: Owned history failure '+id);}}
  const records=builder.records(),failures=builder.failures(),history=builder.history?builder.history():null,cap=phase==='after'?limit:n/2;
  assert.equal(records.length,cap);assert.equal(failures.length,cap);
  const retainedFailures=[];
  for(const stage of fs.readdirSync(root)){
   const file=path.join(root,stage,'failure.json');if(fs.existsSync(file)){const value=JSON.parse(fs.readFileSync(file));const id=value.record.syntheticJobId,artifactName=phase+'-'+name+'-'+id+'.json';fs.copyFileSync(file,path.join(e,'retained-failures',artifactName));retainedFailures.push({id,file:artifactName});}
  }
  assert.equal(retainedFailures.length,n/2);
  results.push({phase,name,limit,requests:n,records,failures,history,retainedFailures:retainedFailures.sort((a,b)=>a.id-b.id),rawStageCount:fs.readdirSync(root).length,rawRoot:root});
 }
 const invalid=[];
 for(const value of [0,257,-1,1.5,true,'4']){const root=path.join(rawRoot,'invalid-'+invalid.length);let error=null;try{implementation('after')({...cfg,root,historyLimit:value,oracle:()=>expected});}catch(e){error=String(e);}assert(error);assert(!fs.existsSync(root));invalid.push({value,rejected:true,rootCreated:false});}
 fs.writeFileSync(path.join(e,'result.json'),JSON.stringify({results,invalid,actualCompilerJobs:0,syntheticRequests:280,scope:'Actual builder JS/receipt/staging with mocked execution; count-bounded retained metadata only'},null,2)+'\n');console.log(JSON.stringify(results.map(r=>({phase:r.phase,name:r.name,records:r.records.length,failures:r.failures.length,history:r.history}))));
})().catch(error=>{console.error(error);process.exitCode=1;});
