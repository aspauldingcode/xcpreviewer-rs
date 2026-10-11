"use strict";
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {runObserved}=require(process.argv[3]);
const out=process.argv[2],python=process.argv[4];fs.mkdirSync(out,{recursive:true});
(async()=>{
 const controls=[];
 for(const mode of ['null-group','negative-parent','invalid-microseconds','missing-group']){
  const dir=path.join(out,mode);fs.mkdirSync(dir);const helper=path.resolve(dir,'owned-malformed-helper');
  const source=`#!${python}
import sys,json,os
roots=[int(a) for a in sys.argv[1:] if a.isdecimal()]
rows=[]
for pid in roots:
 row={'pid':pid,'parent':os.getppid(),'group':os.getppid(),'state':'L','identity':[1,2,'/owned-fixture']}
 if '${mode}'=='null-group':row['group']=None
 if '${mode}'=='negative-parent':row['parent']=-1
 if '${mode}'=='invalid-microseconds':row['identity'][1]=1000000
 if '${mode}'=='missing-group':del row['group']
 rows.append(row)
print(json.dumps(rows))
`;
  fs.writeFileSync(helper,source,{mode:0o700});const sha256=crypto.createHash('sha256').update(source).digest('hex');
  let record,error=null;const start=performance.now();
  try{record=await runObserved(python,['-c','import time;time.sleep(.3)'],{observer:{helper,sha256},supervisorPython:python,timeout:1000});}
  catch(e){error=String(e);record=e.record;}
  assert(record);controls.push({mode,record,error,elapsedMs:performance.now()-start});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({controls,scope:'Malformed owned helper output; no native process identity truth claim'},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
