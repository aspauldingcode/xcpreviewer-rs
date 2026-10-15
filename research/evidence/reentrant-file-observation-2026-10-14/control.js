'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),Module=require('node:module');
const [e,phase,mode,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
const filename=path.resolve(__dirname,'../reloop/source_file_loop.js'),m=new Module(filename,module);m.filename=filename;m.paths=module.paths;m._compile(fs.readFileSync(path.join(e,phase+'.js'),'utf8'),filename);
const {SourceFileLoop}=m.exports,input=path.resolve(__dirname,'../../../research/evidence/source-revision-2026-10-10');
const rows=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json'))),sources=rows.map((_,i)=>fs.readFileSync(path.join(input,i+'-source.swift')));
const expected=i=>fs.readFileSync(path.join(input,i+'-expected.raw'));
const build=i=>({module:fs.readFileSync(path.join(input,i+'-view.wasm')),moduleSha256:rows[i].module_sha256,sourceSha256:rows[i].source_sha256,config:rows[i].config,stride:rows[i].stride});
const file=path.join(out,'owned.swift'),write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
let loop,aborts=0,nested=0;const builds=[];
const builder=(source,{signal})=>{const i=sources.findIndex(s=>s.equals(source));assert(i>=0);builds.push(i);if(i!==1)return Promise.resolve({build:build(i),expected:expected(i)});return new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>{aborts++;write(sources[2]);nested++;void loop[mode]();reject(Error('Owned superseded build'));},{once:true}));};
(async()=>{write(sources[0]);loop=new SourceFileLoop(file,builder);try{
 await loop.poll();assert.deepEqual(loop.snapshot().frame,expected(0));
 write(sources[1]);void loop.poll();assert(loop.status().building);
 write(sources[0]);await loop[mode]();await loop.poll();
 const snapshot=loop.snapshot();assert.deepEqual(await loop.verifyLive(),snapshot);fs.writeFileSync(path.join(out,'frame.raw'),snapshot.frame);
 const winner=phase==='before'?0:2;assert.deepEqual(snapshot.frame,expected(winner));assert(fs.readFileSync(file).equals(sources[2]));
 const result={phase,mode,builds,aborts,nested,winner,revision:snapshot.revision,events:loop.events(),sourceOnDisk:2};await loop.close();result.finalStatus=loop.status();fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
 }finally{await loop.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
