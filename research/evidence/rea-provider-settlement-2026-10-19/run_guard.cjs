'use strict';
const fs=require('node:fs'),crypto=require('node:crypto');
const {runObserved}=require(__dirname+'/observed_compiler.js');
const root=__dirname,plan=JSON.parse(fs.readFileSync(root+'/plan.json'));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
for(const [n,h] of Object.entries({'observed_compiler.js':'9647fff3dbdbfd8e260fb2b566c74c5e1b58b8789877f36c469a7151c5a1f3d6','observed_group_anchor.py':'626377ee7463c0dccc908df14b2afcba99c7454a7e0f25a2c98a024616012014'}))if(hash(root+'/'+n)!==h)throw Error('guard drift');
(async()=>{
 let record,error=null;
 try{record=await runObserved(plan.node_path,[root+'/probe.mjs'],{observer:{helper:'/Users/8amps/xcpreviewer-rs/research/build/libproc-observer/owned-process-snapshot',sha256:'718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'},supervisorPython:'/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',timeout:10000,limit:262144});}
 catch(e){error=String(e);record=e.record||null;}
 fs.writeFileSync(root+'/execution-record.json',JSON.stringify({command:plan.node_path,args:[root+'/probe.mjs'],error,record},null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({error,report:record?.report}));process.exitCode=error?1:0;
})().catch(e=>{console.error(String(e));process.exitCode=1});
