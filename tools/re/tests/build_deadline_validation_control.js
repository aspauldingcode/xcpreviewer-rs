// Actual configuration boundary; compilation prohibited by an intercepted handoff.
'use strict';
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),assert=require('node:assert/strict');
const e=path.resolve(process.argv[2]),prod=path.resolve(process.argv[3]),cfg=JSON.parse(fs.readFileSync(path.join(e,'config.json'))),sentinel=Buffer.from([0,1,2,255,10,42]);let calls=0;
function load(phase){const m=new Module(prod,module);m.filename=prod;m.paths=Module._nodeModulePaths(path.dirname(prod));const original=m.require.bind(m);m.require=id=>id==='./observed_compiler.js'?{runObserved:async()=>{++calls;throw Error('Compiler must not execute');}}:original(id);m._compile(fs.readFileSync(path.join(e,phase+'.js'),'utf8'),prod);return m.exports.rustSourceBuilder;}
const rows=[];
for(const phase of ['before','after']){
 const factory=load(phase),root=path.join(e,phase);fs.mkdirSync(root);
 for(const value of [0,49,5001,-1,1.5,true,'5000'])for(const existing of [false,true]){
  const dir=path.join(root,'invalid-'+rows.length);if(existing){fs.mkdirSync(dir);fs.writeFileSync(path.join(dir,'sentinel'),sentinel);}
  let error=null;try{factory({...cfg,root:dir,timeout:value,oracle:()=>{throw Error('Oracle must not execute');}});}catch(x){error=String(x);}
  assert(error&&error.includes('Bounded Rust build deadline required'));const created=fs.existsSync(dir),files=created?fs.readdirSync(dir):[];
  assert.equal(created,existing||phase==='before');assert.deepEqual(files,existing?['sentinel']:[]);if(existing)assert.deepEqual(fs.readFileSync(path.join(dir,'sentinel')),sentinel);
  rows.push({phase,value,existing,error,rootExists:created,files});
 }
 for(const timeout of [50,5000,null]){
  const dir=path.join(root,'valid-'+rows.length),builder=factory({...cfg,root:dir,...(timeout===null?{}:{timeout}),oracle:()=>{throw Error('Oracle must not execute');}});
  assert(fs.existsSync(dir));assert.deepEqual(fs.readdirSync(dir),[]);assert.deepEqual(builder.budget(),{stageLimit:64,stagesCreated:0});assert.deepEqual(builder.records(),[]);assert.deepEqual(builder.failures(),[]);
  rows.push({phase,value:timeout,valid:true,rootExists:true,files:[],budget:builder.budget(),history:builder.history()});
 }
}
assert.equal(calls,0);fs.writeFileSync(path.join(e,'result.json'),JSON.stringify({rows,syntheticHandoffs:calls,actualCompilerJobs:0},null,2)+'\n');console.log(JSON.stringify({rows:rows.length,calls}));
