// Adversarial packet replay of the sealed owned quarantine fixture; no live server/SDK/native claim.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {PreviewConsumer}=require(process.argv[2]),fixture=JSON.parse(fs.readFileSync(process.argv[3])),out=process.argv[4];
const {previewReadiness}=require(path.join(path.dirname(process.argv[2]),'preview_readiness.js'));
const clone=structuredClone,ready=JSON.parse(fixture.packets[1].packet.result.content[0].text),frame=fixture.packets[2].packet.result;
const stale=fixture.raw_status,recovered=fixture.states[1],recoveredFrame=fixture.packets[9].packet.result;
const status=s=>({content:[{type:'text',text:JSON.stringify({...s,readiness:previewReadiness(s)})}]}),fail={isError:true,content:[{type:'text',text:'Preview operation failed'}]};
const expected=Buffer.alloc(16384,0xc3),changed=Buffer.from(expected);changed.fill(0x77,0,4);
function queueConsumer(){let queue=[],calls=[];const c=new PreviewConsumer(async r=>{calls.push(r.name);const next=queue.shift();assert(next,'Unexpected extra RPC');assert.equal(r.name,next[0]);return clone(next[1]);});return {c,calls,set:q=>{assert.equal(queue.length,0);queue=q;},empty:()=>assert.equal(queue.length,0)};}
async function seed(q){q.set([['preview_status',status(ready)],['preview_frame',frame],['preview_status',status(ready)]]);const a=await q.c.sample();assert.deepEqual(a.frame.allocation,expected);q.empty();return a;}
(async()=>{const rows=[];let bytes=0;
 const cases=['sourceSha256','moduleSha256','allocationSha256','generation','revision','width','stride','renderedBytes','lifecycle','diagnostic','unstable','cold','valid','retry'];
 for(const kind of cases){
  const q=queueConsumer();let a;if(kind!=='cold')a=await seed(q);let s=clone(stale),error=null,result=null;const before=q.calls.length;
  if(['sourceSha256','moduleSha256','allocationSha256'].includes(kind))s.frame[kind]='0'.repeat(64);
  if(['generation','revision','width','stride','renderedBytes'].includes(kind))s.frame[kind]++;
  if(kind==='lifecycle')s.lifecycle.revision=0;
  if(kind==='diagnostic')s.diagnostics.latest.revision=2;
  if(kind==='cold')q.set([['preview_status',status(s)],['preview_frame',fail]]);
  else if(kind==='valid')q.set([['preview_status',status(s)],['preview_status',status(s)]]);
  else if(kind==='retry'){
   q.set([['preview_status',status(s)],['preview_status',status(recovered)],['preview_status',status(recovered)],['preview_frame',recoveredFrame],['preview_status',status(recovered)]]);
  }else if(kind==='unstable'){
   const t=clone(s);t.diagnostics.droppedEvents=1;
   q.set([['preview_status',status(s)],['preview_status',status(t)],['preview_status',status(s)],['preview_status',status(t)]]);
  }else if(['lifecycle','diagnostic'].includes(kind))q.set([['preview_status',status(s)],['preview_status',status(s)]]);
  else q.set([['preview_status',status(s)]]);
  try{result=await q.c.sample();}catch(e){error=String(e);}
  q.empty();const accepted=q.c.snapshot();const success=['valid','retry'].includes(kind);
  assert.equal(error===null,success);if(!success)assert.deepEqual(accepted,a||null);
  if(success){assert.equal(result.status.readiness.state,kind==='valid'?'stale':'ready');assert.equal(result.frame.descriptor.revision,kind==='valid'?1:2);assert.deepEqual(result.frame.allocation,kind==='valid'?expected:changed);}
  if(accepted){const b=accepted.frame.allocation;fs.writeFileSync(path.join(out,kind+'.raw'),b);bytes+=b.length;
   // Returned snapshots must not mutate the privately accepted fallback.
   accepted.frame.allocation.fill(0);accepted.frame.descriptor.sourceSha256='0'.repeat(64);assert.deepEqual(q.c.snapshot().frame.allocation,kind==='retry'?changed:expected);
  }
  rows.push({kind,error,calls:q.calls.slice(before),accepted:accepted?{revision:q.c.snapshot().frame.descriptor.revision,state:q.c.snapshot().status.readiness.state}:null});
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({rows,bytes},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
