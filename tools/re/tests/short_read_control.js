'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {SourceFileLoop}=require('../reloop/source_file_loop.js');
const out=path.resolve(process.argv[2]),mode=process.argv[3],input=path.resolve(process.argv[4]);
const fixture=JSON.parse(fs.readFileSync(path.join(input,'fixtures.json')))[0];
const full=fs.readFileSync(path.join(input,'0-source.swift')),moduleBytes=fs.readFileSync(path.join(input,'0-view.wasm')),expected=fs.readFileSync(path.join(input,'0-expected.raw'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const cases=[];
 for(const [kind,bytes] of [['valid',full],['oversize',Buffer.alloc(4097,65)],['empty',Buffer.alloc(0)]]){
  const root=path.join(out,kind);fs.mkdirSync(root,{recursive:true});const file=path.join(root,'owned.swift');fs.writeFileSync(file,bytes);
  const open=fs.openSync,read=fs.readSync,close=fs.closeSync,owned=new Set(),reads=[],builds=[];let opens=0,closes=0;
  fs.openSync=(name,...args)=>{const fd=open(name,...args);if(name===file){owned.add(fd);opens++;}return fd;};
  fs.readSync=(fd,buffer,offset,length,position)=>{
   if(!owned.has(fd))return read(fd,buffer,offset,length,position);
   const n=read(fd,buffer,offset,Math.min(length,7),position);
   reads.push({offset,requested:length,position,count:n,hex:buffer.subarray(offset,offset+n).toString('hex')});return n;
  };
  fs.closeSync=fd=>{if(owned.delete(fd))closes++;return close(fd);};
  const loop=new SourceFileLoop(file,async source=>{
   builds.push({bytes:source.length,sha256:sha(source)});assert(source.equals(full),'Owned adapter requires complete source');
   return {build:{module:moduleBytes,moduleSha256:fixture.module_sha256,sourceSha256:fixture.source_sha256,config:fixture.config,stride:fixture.stride},expected};
  });
  let snapshot;
  try{await loop.poll();snapshot=loop.snapshot();if(snapshot){assert.deepEqual((await loop.verifyLive()).frame,expected);fs.writeFileSync(path.join(root,'accepted.raw'),snapshot.frame);}}
  finally{await loop.close();fs.openSync=open;fs.readSync=read;fs.closeSync=close;}
  cases.push({kind,sourceBytes:bytes.length,sourceSha256:sha(bytes),opens,closes,reads,builds,events:loop.events(),published:!!snapshot,status:loop.status()});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({mode,cases,scope:'Real owned file reads capped to7 bytes per call; prebuilt owned WASM adapter, no compiler or native Canvas protocol'},null,2)+'\n');
 assert.equal(cases[0].published,mode==='after');assert.equal(cases[1].builds.length,mode==='after'?0:1);assert.equal(cases[2].builds.length,0);
})().catch(error=>{console.error(error);process.exitCode=1;});
