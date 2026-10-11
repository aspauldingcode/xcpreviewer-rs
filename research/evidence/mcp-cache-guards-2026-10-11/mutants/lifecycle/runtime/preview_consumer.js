// Scoped JS consumer for the owned SDK callTool boundary; no native Canvas protocol.
'use strict';
const assert=require('node:assert/strict');
const {decodeFrameContent}=require('./preview_frame_contract.js');
const {previewReadiness}=require('./preview_readiness.js');
class PreviewConsumer {
 #call;#active=false;#accepted=null;
 constructor(callTool){assert.equal(typeof callTool,'function');this.#call=callTool;}
 snapshot(){const a=this.#accepted;return a?{status:structuredClone(a.status),frame:a.frame?{descriptor:{...a.frame.descriptor},allocation:Buffer.from(a.frame.allocation)}:null}:null;}
 async #request(name){const r=await this.#call({name:'preview_'+name,arguments:{}},{timeout:5000});assert(r&&!r.isError,'Preview tool failed');return r;}
 async #status(){const r=await this.#request('status');assert(Array.isArray(r.content)&&r.content.length===1&&r.content[0].type==='text'&&typeof r.content[0].text==='string'&&Buffer.byteLength(r.content[0].text)<=32768);const s=JSON.parse(r.content[0].text);assert.deepEqual(s.readiness,previewReadiness(s));return s;}
 async sample(){
  assert(!this.#active,'Consumer sample active');this.#active=true;
  try{
   if(this.#accepted?.status.readiness.state==='closed')return this.snapshot();
   for(let attempt=0;attempt<2;attempt++){
    const before=await this.#status();
    let frame;
    const cached=this.#accepted?.frame;
    if(cached&&before.frame&&before.lifecycle.liveWorkers===0&&before.readiness.state==='stale'){
     // Reuse only independently accepted bytes with the identical publication identity.
     assert.deepEqual(before.frame,cached.descriptor,'Unavailable publication identity changed');
     frame={descriptor:{...cached.descriptor},allocation:Buffer.from(cached.allocation)};
    }else{
     const r=await this.#request('frame');frame=decodeFrameContent(r.structuredContent);
    }
    const after=await this.#status();
    try{assert.deepEqual(before,after);assert.deepEqual(after.frame,frame?frame.descriptor:null);}catch(_){continue;}
    assert(Number.isSafeInteger(after.lifecycle.revision)&&after.lifecycle.revision>=0,'Invalid lifecycle revision');

    assert(after.readiness.state!=='closed'||frame===null,'Closed preview retained frame');
    const publication=after.diagnostics.latest;
    if(frame&&publication?.kind==='published')assert(
     publication.revision===frame.descriptor.revision&&publication.generation===frame.descriptor.generation&&publication.sourceSha256===frame.descriptor.sourceSha256,
     'Diagnostic publication mismatch');
    if(this.#accepted)assert(after.lifecycle.revision>=this.#accepted.status.lifecycle.revision,
     'Lifecycle revision rollback');
    const previous=this.#accepted?.frame;
    if(previous){
     assert(frame||after.readiness.state==='closed','Accepted frame disappeared while open');
     if(frame){
      assert(frame.descriptor.revision>=previous.descriptor.revision,'Publication rollback');
      if(frame.descriptor.revision===previous.descriptor.revision)assert.deepEqual(frame.descriptor,previous.descriptor,'Publication identity changed');
      else assert(frame.descriptor.generation>previous.descriptor.generation,'Generation rollback');
     }
    }
    this.#accepted={status:structuredClone(after),frame};return this.snapshot();
   }
   throw Error('Preview changed during bounded sample');
  }finally{this.#active=false;}
 }
}
module.exports={PreviewConsumer};
