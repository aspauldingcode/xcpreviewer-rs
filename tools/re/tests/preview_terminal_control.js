'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const {PreviewConsumer}=require(process.argv[2]);
const v=JSON.parse(fs.readFileSync(process.argv[3])).records[0].values;
const queue=ids=>ids.map(i=>structuredClone(v[i]));
(async()=>{
 const outcomes=[];
 for(const kind of ['closed-frame','revision-mismatch']){
  let q=queue([14,15,16]),calls=0;
  const c=new PreviewConsumer(async p=>{calls++;const x=q.shift();assert(x&&p.name==='preview_'+x.name);return x.result;});
  await c.sample();const accepted=c.snapshot();q=queue([14,15,16]);
  for(const i of [0,2]){const x=q[i].result.content[0],s=JSON.parse(x.text);
   if(kind==='closed-frame'){s.lifecycle.closed=true;s.lifecycle.loopClosed=true;s.readiness={state:'closed',frameRevision:2,message:'Preview closed.'};}
   else s.lifecycle.revision=3;
   x.text=JSON.stringify(s);
  }
  let rejected=false;try{await c.sample();}catch(_){rejected=true;}
  outcomes.push({kind,rejected,calls:calls-3,retained:JSON.stringify(c.snapshot().status)===JSON.stringify(accepted.status),allocationBase64:c.snapshot().frame.allocation.toString('base64')});
 }
 let q=queue([14,15,16,22,23,24]),calls=0;
 const c=new PreviewConsumer(async p=>{calls++;const x=q.shift();assert(x&&p.name==='preview_'+x.name);return x.result;});
 await c.sample();const closed=await c.sample();assert.equal(closed.status.readiness.state,'closed');assert.equal(closed.frame,null);assert.deepEqual(await c.sample(),closed);assert.equal(calls,6);
 process.stdout.write(JSON.stringify({outcomes,validClosed:true,terminalNoCalls:true})+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
