'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const {SourceFileLoop}=require(process.argv[3]||'../reloop/source_file_loop.js');
const out=process.argv[2];fs.mkdirSync(out,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const controls=[];
 for(const kind of ['fifo','directory','symlink','missing','regular','fifo-race','symlink-race']){
  const dir=path.join(out,kind);fs.mkdirSync(dir);const file=path.join(dir,'source.swift'),target=path.join(dir,'target.swift');fs.writeFileSync(target,'owned target');
  if(kind==='fifo')execFileSync('/usr/bin/mkfifo',[file],{timeout:1000});
  else if(kind==='directory')fs.mkdirSync(file);
  else if(kind==='symlink')fs.symlinkSync(target,file);
  else if(kind!=='missing')fs.writeFileSync(file,'owned source');
  let builds=0,opened=0,closed=0,raced=false;
  const loop=new SourceFileLoop(file,async()=>{builds++;throw Error('Owned read gate control');});
  const open=fs.openSync,close=fs.closeSync;
  fs.openSync=(name,flags,...rest)=>{
   if(name===file&&kind.endsWith('-race')&&!raced){raced=true;fs.unlinkSync(file);if(kind==='fifo-race')execFileSync('/usr/bin/mkfifo',[file],{timeout:1000});else fs.symlinkSync(target,file);}
   const fd=open(name,flags,...rest);if(name===file)opened++;return fd;
  };
  fs.closeSync=fd=>{closed++;return close(fd);};
  try{
   const start=performance.now();await loop.start(25,500);
   let deadlineAutoClosed=false;
   if(kind==='fifo'){await sleep(650);deadlineAutoClosed=loop.status().loopClosed;assert(deadlineAutoClosed);assert.equal(loop.status().timers,0);}
   await loop.close();const elapsed=performance.now()-start;
   assert(elapsed<1200);assert.equal(builds,kind==='regular'?1:0);assert.equal(opened,closed);
   const status=loop.status();assert.equal(status.timers,0);assert.equal(status.liveWorkers,0);assert.equal(status.building,false);assert.equal(status.loopClosed,true);
   if(kind!=='regular')assert(loop.events().some(e=>e.kind==='unavailable-source'));
   controls.push({kind,builds,opened,closed,raced,deadlineAutoClosed,elapsedMs:elapsed,status});
  }finally{fs.openSync=open;fs.closeSync=close;await loop.close();}
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,scope:'Owned local POSIX regular-file input and pathname replacement controls; no arbitrary filesystem latency or Windows acceptance'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
