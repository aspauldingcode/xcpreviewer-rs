const assert=require('node:assert/strict');const {previewReadiness}=require(process.argv[2]);
const base={schemaVersion:1,lifecycle:{closed:false,loopClosed:false,building:false,busy:false},frame:null,diagnostics:{latest:null,lastFailure:null}};
const frame={revision:2,generation:4},failure={kind:'rejected',generation:3,error:'private compiler path'};
const rows=[];
for(const kind of ['waiting','building','updating','failed','ready-history','stale','invalid','unavailable','closed']){
 const s=structuredClone(base);
 if(['updating','ready-history','stale','invalid','unavailable'].includes(kind))s.frame={...frame};
 if(['building','updating'].includes(kind))s.lifecycle.building=true;
 if(kind==='failed'||kind==='stale')s.diagnostics.latest=failure;
 if(kind==='ready-history'){s.diagnostics.latest={kind:'published',generation:4};s.diagnostics.lastFailure=failure;}
 if(kind==='invalid')s.diagnostics.latest={kind:'invalid-source'};if(kind==='unavailable')s.diagnostics.latest={kind:'unavailable-source'};
 if(kind==='closed')s.lifecycle.loopClosed=true;
 rows.push({kind,input:s,result:previewReadiness(s)});
}
const bad=[];
for(const kind of ['generation','missing-publication','unknown-empty']){
 const s=structuredClone(base);
 if(kind!=='unknown-empty')s.frame={...frame};
 if(kind==='generation')s.diagnostics.latest={kind:'published',generation:3};
 if(kind==='unknown-empty')s.diagnostics.latest={kind:'unrecognized'};
 assert.throws(()=>previewReadiness(s));bad.push({kind,input:s});
}
process.stdout.write(JSON.stringify({rows,bad})+'\n');
