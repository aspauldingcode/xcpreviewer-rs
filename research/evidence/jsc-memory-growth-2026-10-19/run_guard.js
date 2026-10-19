'use strict';
const fs=require('node:fs'),crypto=require('node:crypto');
const {runObserved}=require(__dirname+'/observed_compiler.js');
const root=__dirname,phase=process.argv[2];
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const command=phase==='compile'?'/usr/bin/xcrun':root+'/probe';
let args=phase==='compile'?['clang','-x','objective-c','-fobjc-arc','-framework','Foundation','-framework','JavaScriptCore',root+'/probe.c','-o',root+'/probe']:[];
if(phase==='fixture')args=['--fixture',root+'/owned-documents'];
if(phase.startsWith('output-'))args=['--output-control',phase];
if(!['compile','fixture','output-valid'].includes(phase))throw Error('Unknown phase');
const pins={'observed_compiler.js':'9647fff3dbdbfd8e260fb2b566c74c5e1b58b8789877f36c469a7151c5a1f3d6','observed_group_anchor.py':'626377ee7463c0dccc908df14b2afcba99c7454a7e0f25a2c98a024616012014'};
for(const [p,h] of Object.entries(pins))if(hash(root+'/'+p)!==h)throw Error('Guard changed');
async function main(){
 let record,error=null;
 try{record=await runObserved(command,args,{observer:{helper:'/Users/8amps/xcpreviewer-rs/research/build/libproc-observer/owned-process-snapshot',sha256:'718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'},supervisorPython:'/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',timeout:phase==='compile'?30000:15000,limit:262144});}
 catch(e){error=String(e);record=e.record||null;}
 const row={phase,command,args,source_sha256:hash(root+'/probe.c'),binary_sha256:fs.existsSync(root+'/probe')?hash(root+'/probe'):null,error,record};
 fs.writeFileSync(root+'/'+phase+'-record.json',JSON.stringify(row,null,2)+'\n',{flag:'wx',mode:0o600});
 console.log(JSON.stringify({phase,error,report:record?.report,binary_sha256:row.binary_sha256}));
 process.exitCode=error?1:0;
}
main().catch(e=>{console.error(String(e));process.exitCode=1;});
