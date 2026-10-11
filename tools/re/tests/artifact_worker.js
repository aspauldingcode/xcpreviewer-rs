'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),{spawnSync}=require('node:child_process');
const [mode,root,artifact,helper,python]=process.argv.slice(2);fs.mkdirSync(root,{recursive:true});const file=path.join(root,'input'),original=fs.readFileSync(artifact);fs.writeFileSync(file,original);
if(mode==='empty')fs.truncateSync(file,0);
if(mode==='oversize')fs.truncateSync(file,1048577);
if(mode==='directory'){fs.unlinkSync(file);fs.mkdirSync(file);}
if(mode==='fifo'){fs.unlinkSync(file);const r=spawnSync(python,['-c','import os,sys;os.mkfifo(sys.argv[1])',file],{timeout:1000});if(r.status!==0)throw Error('FIFO fixture failed');}
const realOpen=fs.openSync,realRead=fs.readSync,realClose=fs.closeSync;let opened=0,closed=0,fd=null,mutated=false;
fs.openSync=function(p,...args){if(p===file&&mode==='symlink-swap'){fs.renameSync(file,file+'.original');fs.symlinkSync(artifact,file);}const n=realOpen.call(fs,p,...args);if(p===file&&typeof args[0]==='number'&&(args[0]&fs.constants.O_NONBLOCK)!==0){opened++;fd=n;}return n;};
fs.readSync=function(n,...args){const count=realRead.call(fs,n,...args);if(n===fd&&!mutated&&(mode==='grow'||mode==='mtime')){mutated=true;if(mode==='grow')fs.appendFileSync(file,Buffer.from([1]));else{const bytes=fs.readFileSync(file);bytes[0]^=1;fs.writeFileSync(file,bytes);fs.utimesSync(file,new Date(),new Date(Date.now()+10000));}}return count;};
fs.closeSync=function(n){try{return realClose.call(fs,n);}finally{if(n===fd)closed++;}};
let value=null,error=null;try{value=require(helper).readArtifact(file);}catch(e){error=String(e);}
process.stdout.write(JSON.stringify({mode,opened,closed,accepted:value!==null,bytes:value?.length??0,sha:value?crypto.createHash('sha256').update(value).digest('hex'):null,error,mutated}));
