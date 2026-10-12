// Actual builder retention with owned error text and synthetic execution handoff.
'use strict';
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),assert=require('node:assert/strict');
const e=path.resolve(process.argv[2]),prod=path.resolve(process.argv[3]),cfg=JSON.parse(fs.readFileSync(path.join(e,'config.json'))),source=fs.readFileSync(path.join(e,'source.swift'));let calls=0;
const cases=[['ascii-under','x'.repeat(1016)],['ascii-exact','x'.repeat(1017)],['ascii-over','x'.repeat(1018)],['emoji','🙂'.repeat(400)],['accent','é'.repeat(700)],['log','Owned failure']];
(async()=>{const rows=[];
for(const phase of ['before','after'])for(const [name,message] of cases){
 const original=Error(message),log=Error('🙂'.repeat(400));let writes=0;const proxy=new Proxy(fs,{get(target,key){if(key==='writeFileSync')return (file,...args)=>{if(path.basename(file)==='failure.json'){++writes;if(name==='log')throw log;}return target.writeFileSync(file,...args);};return target[key];}});
 const m=new Module(prod,module);m.filename=prod;m.paths=Module._nodeModulePaths(path.dirname(prod));const req=m.require.bind(m);m.require=id=>id==='node:fs'?proxy:id==='./observed_compiler.js'?{runObserved:async()=>{++calls;throw original;}}:req(id);m._compile(fs.readFileSync(path.join(e,phase+'.js'),'utf8'),prod);
 const root=path.join(e,phase+'-'+name),builder=m.exports.rustSourceBuilder({...cfg,root,oracle:()=>{throw Error('No oracle');}});let caught;try{await builder(source,{signal:new AbortController().signal});}catch(x){caught=x;}assert.strictEqual(caught,original);const stage=fs.readdirSync(root)[0],failure=builder.failures()[0],files=fs.readdirSync(path.join(root,stage)).sort();assert.equal(writes,1);assert.deepEqual(builder.records(),[]);assert.deepEqual(builder.budget(),{stageLimit:64,stagesCreated:1});assert.deepEqual(fs.readFileSync(path.join(root,stage,'source.swift')),source);if(name!=='log')assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root,stage,'failure.json'))),failure);
 rows.push({phase,name,stage,files,failure,originalPreserved:caught===original,originalBytes:Buffer.byteLength(String(original)),logOriginalBytes:name==='log'?Buffer.byteLength(String(log)):null,budget:builder.budget(),writes});
}
fs.writeFileSync(path.join(e,'result.json'),JSON.stringify({rows,syntheticHandoffs:calls,actualCompilerJobs:0},null,2)+'\n');console.log(JSON.stringify({controls:12,calls}));})().catch(x=>{console.error(x);process.exitCode=1;});
