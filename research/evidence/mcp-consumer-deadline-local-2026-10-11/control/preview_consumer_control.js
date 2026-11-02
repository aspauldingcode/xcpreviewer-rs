// Correlated fixture replies, independently selected hostile histories.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const {PreviewConsumer}=require(process.argv[2]);const values=JSON.parse(fs.readFileSync(process.argv[3])).records[0].values;
const queue=indices=>indices.map(i=>structuredClone(values[i]));
const good=queue([4,5,6]),newer=queue([14,15,16]),last=queue([22,23,24]);
(async()=>{
 const outcomes=[];
 for(const kind of ['rollback','generation','identity','race-limit','availability','hash','readiness','tool-error']){
  let q=[...good,...newer],calls=0;
  const c=new PreviewConsumer(async p=>{calls++;const r=q.shift();assert(r&&p.name==='preview_'+r.name);return r.result});
  await c.sample();await c.sample();const accepted=c.snapshot();
  if(kind==='rollback')q=queue([4,5,6]);
  else if(kind==='generation'){
   q=structuredClone(last);q[1].result.structuredContent.frame.descriptor.generation=2;
   for(const i of [0,2]){const r=q[i].result.content[0],s=JSON.parse(r.text);s.frame.generation=2;s.diagnostics.latest.generation=2;r.text=JSON.stringify(s);}
  }else if(kind==='identity'){
   q=structuredClone(newer);q[1].result.structuredContent.frame.descriptor.width=12;
   for(const i of [0,2]){const r=q[i].result.content[0],s=JSON.parse(r.text);s.frame.width=12;r.text=JSON.stringify(s);}
  }else if(kind==='race-limit')q=queue([10,12,13,10,12,13]);
  else if(kind==='availability'){
   q=queue([14,15,16,14,15,16]);for(const i of [1,4])q[i].result.structuredContent={available:false,frame:null};
  }else if(kind==='hash'){
   q=structuredClone(newer);const f=q[1].result.structuredContent.frame,b=Buffer.from(f.allocationBase64,'base64');b[52]^=1;f.allocationBase64=b.toString('base64');
  }else if(kind==='readiness'){
   q=structuredClone(newer);const r=q[0].result.content[0],s=JSON.parse(r.text);s.readiness.state='failed';r.text=JSON.stringify(s);
  }else q=[{name:'status',result:{isError:true,content:[{type:'text',text:'Preview operation failed'}]}}];
  const before=calls;await assert.rejects(()=>c.sample());assert.deepEqual(c.snapshot(),accepted);outcomes.push({kind,rejected:true,calls:calls-before,retainedRevision:c.snapshot().frame.descriptor.revision});
 }
 let q=queue([4,5,6]),release;const held=new Promise(r=>release=r),c=new PreviewConsumer(async p=>{await held;const r=q.shift();assert(p.name==='preview_'+r.name);return r.result});
 const pending=c.sample();await assert.rejects(()=>c.sample(),/active/);release();await pending;const copied=c.snapshot();copied.frame.allocation.fill(0);copied.status.frame.width=1;assert.equal(c.snapshot().status.frame.width,13);
 process.stdout.write(JSON.stringify({outcomes,concurrentRejected:true,detached:true})+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
