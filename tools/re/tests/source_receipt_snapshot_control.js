'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {SourceRevisionHost}=require(process.argv[2]);
const out=process.argv[3],observe=process.argv[4]==='observe';
const fixtures=process.argv[5] || path.resolve(__dirname,'../../../research/evidence/source-revision-2026-10-10');
const rows=JSON.parse(fs.readFileSync(path.join(fixtures,'fixtures.json')));
const source=i=>fs.readFileSync(path.join(fixtures,i+'-source.swift'));
const moduleBytes=i=>fs.readFileSync(path.join(fixtures,i+'-view.wasm'));
const frame=i=>fs.readFileSync(path.join(fixtures,i+'-expected.raw'));
const build=i=>({module:moduleBytes(i),moduleSha256:rows[i].module_sha256,sourceSha256:rows[i].source_sha256,config:rows[i].config,stride:rows[i].stride});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const results=[];
 for(const mode of ['changing-module-reject','changing-module-accept','receipt-getter-mutates-input']){
  const h=new SourceRevisionHost();
  try{
   const first=await h.submit(h.begin(source(0)),build(0),frame(0)),baseline=h.snapshot(),ticket=h.begin(source(0));
   let reads=0;const a=moduleBytes(0),b=moduleBytes(1),receipt=build(0);
   Object.defineProperty(receipt,'module',{get(){return ++reads<=2?a:b;}});
   if(mode==='receipt-getter-mutates-input'){
    Object.defineProperty(receipt,'module',{get(){++reads;return a;}});
    Object.defineProperty(receipt,'moduleSha256',{get(){a.fill(0);return rows[0].module_sha256;}});
   }
   const expected=mode==='changing-module-reject'?frame(1):frame(0);
   let value,error;try{value=await h.submit(ticket,receipt,expected);}catch(e){error=String(e);}
   const accepted=!!value,snapshot=h.snapshot();
   let passed;
   if(mode==='changing-module-reject')passed=!accepted&&JSON.stringify(snapshot)===JSON.stringify(baseline)&&reads===1;
   else passed=accepted&&value.moduleSha256===rows[0].module_sha256&&value.sourceRevision.sourceSha256===rows[0].source_sha256&&value.frame.equals(frame(0))&&reads===1;
   if(accepted)assert.deepEqual(await h.verifyLive(),value);else assert.deepEqual(await h.verifyLive(),baseline);
   results.push({mode,module_property_reads:reads,accepted,error:error||null,published_module_sha256:snapshot?.moduleSha256,declared_module_sha256:rows[0].module_sha256,receipt_matches_published_module:!accepted||snapshot.moduleSha256===rows[0].module_sha256,full_frame_bytes_verified:16384,live_workers_before_close:h.status().liveWorkers,passed});
  }finally{await h.close();assert.equal(h.status().liveWorkers,0);}
 }
 for(const mode of ['non-ascii-overridden-every','valid-source-mutating-every']){
  const h=new SourceRevisionHost();let calls=0,value,error;const bytes=source(0);
  if(mode==='non-ascii-overridden-every')bytes[0]=255;
  bytes.every=()=>{++calls;if(mode==='valid-source-mutating-every')bytes.fill(255);return true;};
  try{try{value=h.begin(bytes);}catch(e){error=String(e);}
   const passed=mode==='non-ascii-overridden-every'?!value&&calls===0:!!value&&value.sourceSha256===rows[0].source_sha256&&calls===0;
   results.push({mode,source_override_calls:calls,accepted:!!value,error:error||null,source_hash_matches_original:!!value&&value.sourceSha256===rows[0].source_sha256,full_frame_bytes_verified:0,passed});
  }finally{await h.close();assert.equal(h.status().liveWorkers,0);}
 }
 fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({node:process.version,v8:process.versions.v8,results,failures:results.filter(x=>!x.passed).length,final_owned_workers:0,scope:'Owned JS source/module receipt snapshot policy, not native Canvas or artifact authenticity'},null,2)+'\n');
 if(!observe)assert(results.every(x=>x.passed));
})().catch(e=>{console.error(e);process.exitCode=1;});
