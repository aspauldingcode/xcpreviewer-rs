// Finite historical SDK packet fixture, not a fresh SDK/native execution.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const {PreviewConsumer}=require(process.argv[2]);const v=JSON.parse(fs.readFileSync(process.argv[3])).records[0].values;
const queue=ids=>ids.map(i=>structuredClone(v[i]));
(async()=>{
 const outcomes=[];
 for(const revision of [0,1]){
  let q=queue([14,15,16]),calls=0;
  const c=new PreviewConsumer(async p=>{calls++;const x=q.shift();assert(x&&p.name==='preview_'+x.name);return x.result;});
  await c.sample();const before=c.snapshot();q=queue([22,23,24]);
  for(const i of [0,2]){const packet=q[i].result.content[0];const s=JSON.parse(packet.text);s.lifecycle.revision=revision;packet.text=JSON.stringify(s);}
  let rejected=false;try{await c.sample();}catch(_){rejected=true;}
  const after=c.snapshot(),used=calls-3;q=queue([14,15,16]);const initial=calls;const recovery=await c.sample();
  outcomes.push({revision,rejected,calls:used,retained:JSON.stringify(after.status)===JSON.stringify(before.status),beforeAllocationBase64:before.frame.allocation.toString('base64'),afterRevision:after.status.lifecycle.revision,afterClosed:after.status.readiness.state==='closed',afterAllocationBase64:after.frame?.allocation.toString('base64')??null,recoveryCalls:calls-initial,recoveryRevision:recovery.status.lifecycle.revision,recoveryClosed:recovery.status.readiness.state==='closed',recoveryAllocationBase64:recovery.frame?.allocation.toString('base64')??null});
 }
 let q=queue([14,15,16,18,19,20,22,23,24]),calls=0;const c=new PreviewConsumer(async p=>{calls++;const x=q.shift();assert(x&&p.name==='preview_'+x.name);return x.result;});
 const ready=await c.sample(),stale=await c.sample(),closed=await c.sample();assert.deepEqual(stale.frame,ready.frame);assert.equal(closed.status.lifecycle.revision,2);assert.equal(closed.frame,null);assert.deepEqual(await c.sample(),closed);assert.equal(calls,9);
 process.stdout.write(JSON.stringify({outcomes,validClosed:true,validStale:true,terminalNoCalls:true,validAllocationBase64:ready.frame.allocation.toString('base64')})+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
