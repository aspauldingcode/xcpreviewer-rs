'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),Module=require('node:module');
const [e,phase,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
const filename=path.resolve(__dirname,'../reloop/source_file_loop.js'),m=new Module(filename,module);m.filename=filename;m.paths=module.paths;m._compile(fs.readFileSync(path.join(e,phase+'.js'),'utf8'),filename);
const {SourceFileLoop}=m.exports,input=path.resolve(__dirname,'../../../research/evidence/source-revision-2026-10-10');
const rows=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json'))),sources=rows.map((_,i)=>fs.readFileSync(path.join(input,i+'-source.swift')));
const expected=i=>fs.readFileSync(path.join(input,i+'-expected.raw'));
const build=i=>({module:fs.readFileSync(path.join(input,i+'-view.wasm')),moduleSha256:rows[i].module_sha256,sourceSha256:rows[i].source_sha256,config:rows[i].config,stride:rows[i].stride});
const file=path.join(out,'owned.swift'),write=b=>{fs.writeFileSync(file+'.new',b);fs.renameSync(file+'.new',file);};
(async()=>{const cases=[];
 for(const kind of ['opaque','ordinary']){
  let loop;const builds=[];
  const builder=async source=>{const i=sources.findIndex(s=>s.equals(source));assert(i>=0);builds.push(i);if(i===1)throw kind==='opaque'?Object.create(null):Error('Owned builder failure');return {build:build(i),expected:expected(i)};};
  write(sources[0]);loop=new SourceFileLoop(file,builder);
  try{await loop.poll();const baseline=loop.snapshot();assert.deepEqual(baseline.frame,expected(0));
   write(sources[1]);let pollError=null,verifyError=null;try{await loop.poll();}catch(e){pollError=String(e);}assert.deepEqual(loop.snapshot(),baseline);
   try{assert.deepEqual(await loop.verifyLive(),baseline);}catch(e){verifyError=String(e);}
   fs.writeFileSync(path.join(out,kind+'-retained.raw'),loop.snapshot().frame);
   write(sources[2]);await loop.poll();const recovery=loop.snapshot();assert.deepEqual(recovery.frame,expected(2));assert.deepEqual(await loop.verifyLive(),recovery);
   fs.writeFileSync(path.join(out,kind+'-recovery.raw'),recovery.frame);
   const row={kind,builds,pollError,verifyError,diagnostics:loop.diagnostics(),events:loop.events(),revision:recovery.revision};await loop.close();row.finalStatus=loop.status();cases.push(row);
  }finally{await loop.close();}
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({phase,cases},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
