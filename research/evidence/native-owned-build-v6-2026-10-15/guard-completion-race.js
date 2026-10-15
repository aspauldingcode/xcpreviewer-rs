'use strict';
const {runObserved}=require('/Users/8amps/xcpreviewer-rs/tools/re/reloop/observed_compiler.js');
const fs=require('fs'),crypto=require('crypto');
const r='/Users/8amps/xcpreviewer-rs';
(async()=>{
 const results=[];
 for(let i=0;i<8;i++){
  let record,error=null;const rows=[];
  try{record=await runObserved('/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',['-S','-c','import time; time.sleep(0.05)'],{observer:{helper:r+'/research/build/libproc-observer/owned-process-snapshot',sha256:'718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'},supervisorPython:'/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',timeout:1000,limit:65536,onObservation:v=>{rows.push(...v);}});}catch(e){error=String(e);record=e.record||null;}
  results.push({i,error,record,observed_rows:rows});
 }
 fs.writeFileSync('/private/tmp/guard-completion-race.json',JSON.stringify({scope:'Eight sequential owned short-lived Python controls; no compiler, UI or native Canvas evidence',results},null,2)+'\n',{mode:0o600});
 process.stdout.write(JSON.stringify(results.map(x=>({i:x.i,error:x.error,report:x.record?.report})))+'\n');
})();
