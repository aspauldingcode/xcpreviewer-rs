// Actual builder filesystem/error handling with explicitly injected failures.
'use strict';
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),assert=require('node:assert/strict');
const e=path.resolve(process.argv[2]),prod=path.resolve(process.argv[3]),cfg=JSON.parse(fs.readFileSync(path.join(e,'config.json'))),source=fs.readFileSync(path.join(e,'source.swift'));let calls=0,oracleCalls=0;
(async()=>{const rows=[];
for(const phase of ['before','after'])for(const mode of ['normal','ENOSPC','EACCES']){
 const originalError=Error('Owned build execution failure');originalError.record={scope:'Synthetic execution boundary',id:rows.length};const writeError=Error('Owned failure log '+mode);writeError.code=mode;let writes=0;
 const proxy=new Proxy(fs,{get(target,key){if(key==='writeFileSync')return (file,...args)=>{if(path.basename(file)==='failure.json'){++writes;if(mode!=='normal')throw writeError;}return target.writeFileSync(file,...args);};return target[key];}});
 const m=new Module(prod,module);m.filename=prod;m.paths=Module._nodeModulePaths(path.dirname(prod));const requireOriginal=m.require.bind(m);m.require=id=>id==='node:fs'?proxy:id==='./observed_compiler.js'?{runObserved:async()=>{++calls;throw originalError;}}:requireOriginal(id);m._compile(fs.readFileSync(path.join(e,phase+'.js'),'utf8'),prod);
 const root=path.join(e,phase+'-'+mode),builder=m.exports.rustSourceBuilder({...cfg,root,oracle:()=>{++oracleCalls;throw Error('No oracle');}});let caught=null;try{await builder(source,{signal:new AbortController().signal});}catch(x){caught=x;}
 assert(caught);assert.equal(caught===originalError,phase==='after'||mode==='normal');assert.equal(writes,1);assert.deepEqual(builder.records(),[]);assert.deepEqual(builder.budget(),{stageLimit:64,stagesCreated:1});const stage=fs.readdirSync(root)[0],base=path.join(root,stage);assert.deepEqual(fs.readFileSync(path.join(base,'source.swift')),source);const failure=builder.failures()[0];assert.equal(failure.error,String(originalError));assert.deepEqual(failure.record,originalError.record);const persisted=fs.existsSync(path.join(base,'failure.json'));
 assert.equal(persisted,mode==='normal');assert.equal(failure.persistence_error,phase==='after'&&mode!=='normal'?String(writeError):undefined);if(persisted)assert.deepEqual(JSON.parse(fs.readFileSync(path.join(base,'failure.json'))),failure);
 rows.push({phase,mode,caught:String(caught),originalPreserved:caught===originalError,writes,persisted,stage,budget:builder.budget(),failure,records:builder.records(),files:fs.readdirSync(base).sort()});
}
assert.equal(calls,6);assert.equal(oracleCalls,0);fs.writeFileSync(path.join(e,'result.json'),JSON.stringify({rows,syntheticHandoffs:calls,oracleCalls,actualCompilerJobs:0},null,2)+'\n');console.log(JSON.stringify({controls:6,calls,oracleCalls}));})().catch(x=>{console.error(x);process.exitCode=1;});
