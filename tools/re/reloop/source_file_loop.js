'use strict';
// Owned finite file polling. Builder must honor AbortSignal and settle on abort.
const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {SourceRevisionHost}=require('./source_revision_host.js');
class SourceFileLoop {
 #host=new SourceRevisionHost();#builder;#file;#seen=null;#pending=null;#drain=Promise.resolve();#running=false;#abort=null;#closed=false;#pollTimer=null;#deadline=null;#events=[];#dropped=0;
 constructor(file,builder){assert.equal(typeof file,'string');assert.equal(typeof builder,'function');this.#file=file;this.#builder=builder;}
 events(){return this.#events.map(e=>({...e}));}
 diagnostics(){
  const events=this.events(),failure=[...events].reverse().find(e=>['rejected','invalid-source','unavailable-source'].includes(e.kind));
  return {retainedEvents:events.length,droppedEvents:this.#dropped,latest:events.length?{...events[events.length-1]}:null,lastFailure:failure?{...failure}:null};
 }
 #record(event){
  if(typeof event.error==='string'){
   let error='',bytes=0;
   // Bound work before UTF-8 accounting; preserve complete code points.
   for(const char of event.error.slice(0,1024).replace(/[\u0000-\u001f\u007f]/g,' ')){
    const size=Buffer.byteLength(char);if(bytes+size>512)break;error+=char;bytes+=size;
   }
   event={...event,error};
  }
  if(this.#events.length===64){this.#events.shift();this.#dropped=Math.min(Number.MAX_SAFE_INTEGER,this.#dropped+1);}
  this.#events.push(event);
 }
 snapshot(){return this.#host.snapshot();}
 async verifyLive(){await this.#drain;try{return await this.#host.verifyLive();}finally{this.#kick();}}
 status(){return {...this.#host.status(),loopClosed:this.#closed,building:this.#running,timers:Number(!!this.#pollTimer)+Number(!!this.#deadline)};}
 start(interval=25,duration=5000){
  assert(!this.#closed&&!this.#pollTimer);assert(Number.isSafeInteger(interval)&&interval>=10&&interval<=250);assert(Number.isSafeInteger(duration)&&duration>=500&&duration<=10000);
  this.#pollTimer=setInterval(()=>this.poll(),interval);
  this.#deadline=setTimeout(()=>{void this.close();},duration);
  return this.poll();
 }
 poll(){return this.#observe(false);}
 refresh(){assert(!this.#closed,'File loop closed');return this.#observe(true);}
 #observe(force){
  if(this.#closed)return this.#drain;
  let source,key,reason;
  try{
   assert(fs.lstatSync(this.#file).isFile(),'Regular source file required');
   const {O_RDONLY,O_NONBLOCK,O_NOFOLLOW}=fs.constants;
   assert(Number.isInteger(O_NONBLOCK)&&Number.isInteger(O_NOFOLLOW),'Nonblocking no-follow source open unavailable');
   const fd=fs.openSync(this.#file,O_RDONLY|O_NONBLOCK|O_NOFOLLOW);
   try{
    // Recheck the opened object: the pathname can change after lstat().
    assert(fs.fstatSync(fd).isFile(),'Opened source must be regular');
    source=Buffer.alloc(4097);source=source.subarray(0,fs.readSync(fd,source,0,4097,0));
   }finally{fs.closeSync(fd);}
   key=crypto.createHash('sha256').update(source).digest('hex');
   if(!source.length||source.length>4096||!source.every(b=>b<128))reason='invalid-source';
  }catch(e){key='read-error:'+String(e.code||e.message);reason='unavailable-source';}
  if(key===this.#seen&&(!force||reason)){this.#kick();return this.#drain;}
  this.#seen=key;this.#pending=null;
  if(reason){this.#host.invalidate();this.#record({kind:reason});return this.#drain;}
  const ticket=this.#host.begin(source);this.#pending={source:Buffer.from(source),ticket};
  this.#record({kind:'observed',generation:ticket.generation,sourceSha256:ticket.sourceSha256});
  this.#kick();
  return this.#drain;
 }
 #kick(){if(!this.#closed&&!this.#running&&this.#pending&&!this.#host.status().busy){this.#running=true;this.#drain=this.#pump();}}
 async #pump(){
  try{
   while(!this.#closed&&this.#pending){
    const job=this.#pending;this.#pending=null;this.#abort=new AbortController();
    try{
     const result=await this.#builder(job.source,{signal:this.#abort.signal});
     if(this.#closed)throw Error('File loop closed before publication');
     const frame=await this.#host.submit(job.ticket,result.build,result.expected);
     this.#record({kind:'published',generation:job.ticket.generation,revision:frame.revision,sourceSha256:job.ticket.sourceSha256});
    }catch(e){this.#record({kind:'rejected',generation:job.ticket.generation,error:String(e)});}
    finally{this.#abort=null;}
   }
  }finally{this.#running=false;}
 }
 async close(){
  this.#closed=true;this.#pending=null;
  clearInterval(this.#pollTimer);clearTimeout(this.#deadline);this.#pollTimer=this.#deadline=null;
  this.#abort?.abort();
  await Promise.all([this.#drain,this.#host.close()]);
 }
}
module.exports={SourceFileLoop};
