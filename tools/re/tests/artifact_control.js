'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),{spawnSync}=require('node:child_process');
const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});const expected=fs.readFileSync(cfg.module),controls=[];
for(const mode of ['valid','empty','oversize','directory','fifo','symlink-swap','grow','mtime']){
 const start=Date.now(),r=spawnSync(process.execPath,[path.join(__dirname,'artifact_worker.js'),mode,path.join(out,mode),cfg.module,cfg.helper,cfg.python],{timeout:2000,maxBuffer:65536});assert.equal(r.status,0,r.stderr?.toString());assert.equal(r.signal,null);const row=JSON.parse(r.stdout);assert.equal(row.opened,row.closed);assert.equal(row.accepted,mode==='valid');
 if(mode==='valid'){assert.equal(row.bytes,expected.length);assert.equal(row.sha,crypto.createHash('sha256').update(expected).digest('hex'));}else assert(row.error);
 if(['grow','mtime'].includes(mode))assert(row.mutated);controls.push({...row,elapsedMs:Date.now()-start});
}
fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,expectedBytes:expected.length,expectedSha:crypto.createHash('sha256').update(expected).digest('hex'),scope:'Actual owned filesystem artifact read controls; final-component no-follow, nonblocking descriptor and read identity, not general sandboxing or native Canvas transport'},null,2)+'\n');
