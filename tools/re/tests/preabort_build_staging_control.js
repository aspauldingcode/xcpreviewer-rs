// Actual JS/filesystem pre-abort control; all native child spawns intercepted.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),Module=require('node:module'),cp=require('node:child_process');
const e=path.resolve(process.argv[2]),production=path.resolve(process.argv[3]),config=JSON.parse(fs.readFileSync(path.join(e,'config.json'))),source=fs.readFileSync(path.join(e,'source.swift'));let intercepted=0;
cp.spawn=()=>{++intercepted;throw Error('Owned noncancelled spawn intercept');};
function implementation(phase){const m=new Module(production,module);m.filename=production;m.paths=Module._nodeModulePaths(path.dirname(production));m._compile(fs.readFileSync(path.join(e,'rust-builder-'+phase+'.js'),'utf8'),production);return m.exports.rustSourceBuilder;}
(async()=>{
 const results=[];
 for(const phase of ['before','after']){
  const root=path.join(e,phase),builder=implementation(phase)({...config,root,oracle:()=>{throw Error('Oracle must not run');}}),errors=[];const start=intercepted;
  for(let i=0;i<4;i++){const a=new AbortController();a.abort();try{await builder(source,{signal:a.signal});throw Error('Cancelled build admitted');}catch(error){errors.push(String(error));}}
  assert.equal(intercepted,start);const preStages=fs.readdirSync(root).filter(name=>name.startsWith('build-'));const preFailures=builder.failures();
  assert.equal(preStages.length,phase==='before'?4:0);assert.equal(preFailures.length,phase==='before'?4:0);
  for(const stage of preStages)assert.deepEqual(fs.readFileSync(path.join(root,stage,'source.swift')),source);
  let positiveError=null;try{await builder(source,{signal:new AbortController().signal});}catch(error){positiveError=String(error);}
  assert.equal(intercepted-start,1);assert.equal(positiveError,'Error: Owned noncancelled spawn intercept');const finalStages=fs.readdirSync(root).filter(name=>name.startsWith('build-'));assert.equal(finalStages.length,preStages.length+1);
  results.push({phase,cancelledRequests:4,errors,preStages,preFailureCount:preFailures.length,preStagedSourceBytes:preStages.length*source.length,preSpawnCount:0,positiveError,interceptedNoncancelledSpawns:1,finalStages,records:builder.records(),failures:builder.failures()});
 }
 fs.writeFileSync(path.join(e,'result.json'),JSON.stringify({results,actualChildSpawns:0,scope:'Actual JS/filesystem with native spawn intercepted; not actual compiler cancellation'},null,2)+'\n');console.log(JSON.stringify(results.map(r=>({phase:r.phase,preStages:r.preStages.length,bytes:r.preStagedSourceBytes,positiveSpawns:r.interceptedNoncancelledSpawns}))));
})().catch(error=>{console.error(error);process.exitCode=1;});
