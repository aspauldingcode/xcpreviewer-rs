// Actual builder failure retention; injected record ownership/serialization controls.
'use strict';
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),assert=require('node:assert/strict');
const e=path.resolve(process.argv[2]),prod=path.resolve(process.argv[3]),cfg=JSON.parse(fs.readFileSync(path.join(e,'config.json'))),source=fs.readFileSync(path.join(e,'source.swift'));let calls=0;
(async()=>{const rows=[];
for(const phase of ['before','after'])for(const mode of ['mutable','cycle','bigint','getter','absent']){
 const original=Error('Owned execution failure '+mode),getterError=Error('Owned record getter failure');if(mode==='mutable')original.record={scope:'Owned record',value:1};if(mode==='cycle'){original.record={scope:'Owned cycle'};original.record.self=original.record;}if(mode==='bigint')original.record={value:1n};if(mode==='getter')Object.defineProperty(original,'record',{get(){throw getterError;}});
 const m=new Module(prod,module);m.filename=prod;m.paths=Module._nodeModulePaths(path.dirname(prod));const req=m.require.bind(m);m.require=id=>id==='./observed_compiler.js'?{runObserved:async()=>{++calls;throw original;}}:req(id);m._compile(fs.readFileSync(path.join(e,phase+'.js'),'utf8'),prod);const root=path.join(e,phase+'-'+mode),builder=m.exports.rustSourceBuilder({...cfg,root,oracle:()=>{throw Error('No oracle');}});let caught;try{await builder(source,{signal:new AbortController().signal});}catch(x){caught=x;}
 assert.strictEqual(caught,phase==='before'&&mode==='getter'?getterError:original);if(mode==='mutable')original.record.value=2;let failures=null,readError=null;try{failures=builder.failures();}catch(x){readError=String(x);}
 const stage=fs.readdirSync(root)[0],base=path.join(root,stage),files=fs.readdirSync(base).sort(),disk=files.includes('failure.json')?JSON.parse(fs.readFileSync(path.join(base,'failure.json'))):null;assert.deepEqual(fs.readFileSync(path.join(base,'source.swift')),source);assert.deepEqual(builder.budget(),{stageLimit:64,stagesCreated:1});assert.deepEqual(builder.records(),[]);
 if(phase==='after'){assert.equal(readError,null);assert.equal(failures.length,1);assert.deepEqual(disk,failures[0]);if(mode==='mutable')assert.equal(failures[0].record.value,1);}
 rows.push({phase,mode,stage,files,caught:String(caught),originalPreserved:caught===original,readError,failures,disk,budget:builder.budget(),records:builder.records()});
}
fs.writeFileSync(path.join(e,'result.json'),JSON.stringify({rows,syntheticHandoffs:calls,actualCompilerJobs:0},null,2)+'\n');console.log(JSON.stringify({controls:10,calls}));})().catch(x=>{console.error(x);process.exitCode=1;});
