'use strict';
// Local finite primary-renderer consumer API. No network/MCP transport claimed.
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {SourceFileLoop}=require('./source_file_loop.js');
const {previewReadiness}=require('./preview_readiness.js');
class PreviewSession {
 #loop;#operation=false;
 constructor(file,builder){this.#loop=new SourceFileLoop(file,builder);}
 #describe(snapshot){
  if(!snapshot)return null;
  assert(snapshot.sourceRevision&&snapshot.geometry);
  return {revision:snapshot.revision,generation:snapshot.sourceRevision.generation,
   sourceSha256:snapshot.sourceRevision.sourceSha256,moduleSha256:snapshot.moduleSha256,
   allocationSha256:crypto.createHash('sha256').update(snapshot.frame).digest('hex'),
   allocationBytes:snapshot.frame.length,renderedBytes:snapshot.geometry.height*snapshot.geometry.stride,
   ...snapshot.geometry,format:'premultiplied-RGBA8'};
 }
 status(){const status={schemaVersion:1,scope:'Finite primary source preview; local owned policy',
  lifecycle:this.#loop.status(),frame:this.#describe(this.#loop.snapshot()),diagnostics:this.#loop.diagnostics()};return {...status,readiness:previewReadiness(status)};}
 async #run(action){assert(!this.#operation,'Preview session operation active');this.#operation=true;try{return await action();}finally{this.#operation=false;}}
 async start(interval=25,duration=5000){return this.#run(async()=>{await this.#loop.start(interval,duration);return this.status();});}
 async poll(){return this.#run(async()=>{await this.#loop.poll();return this.status();});}
 async refresh(){return this.#run(async()=>{await this.#loop.refresh();return this.status();});}
 async readFrame(){return this.#run(async()=>{
  if(!this.#loop.snapshot())return null;
  const snapshot=await this.#loop.verifyLive();return {descriptor:this.#describe(snapshot),allocation:Buffer.from(snapshot.frame)};
 });}
 async close(){await this.#loop.close();return this.status();}
}
module.exports={PreviewSession};
