const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {FRAME_OUTPUT_SCHEMA,frameContent,decodeFrameContent}=require(process.argv[2]);
const allocation=Buffer.from(Array.from({length:16384},(_,i)=>(i*23+11)&255));
const descriptor={revision:1,generation:2,sourceSha256:'a'.repeat(64),moduleSha256:'b'.repeat(64),allocationSha256:crypto.createHash('sha256').update(allocation).digest('hex'),allocationBytes:16384,renderedBytes:128,width:3,height:2,stride:64,format:'premultiplied-RGBA8'};
const present=frameContent({descriptor,allocation}),absent=frameContent(null);assert.equal(decodeFrameContent(absent),null);assert.deepEqual(decodeFrameContent(present).allocation,allocation);
const cases=[];
for(const kind of ['false-present','true-null','missing','extent','geometry','hash','base64','extra']){
 const v=structuredClone(present);
 if(kind==='false-present')v.available=false;else if(kind==='true-null')v.frame=null;else if(kind==='missing')delete v.available;
 else if(kind==='extent')v.frame.descriptor.allocationBytes=16383;else if(kind==='geometry')v.frame.descriptor.renderedBytes=64;
 else if(kind==='hash')v.frame.descriptor.allocationSha256='c'.repeat(64);else if(kind==='base64')v.frame.allocationBase64+='A';else v.frame.extra=1;
 assert.throws(()=>decodeFrameContent(v));cases.push({kind,content:v});
}
const detached=decodeFrameContent(present);detached.allocation[0]^=1;detached.descriptor.width=16;assert.deepEqual(decodeFrameContent(present).allocation,allocation);assert.equal(present.frame.descriptor.width,3);
process.stdout.write(JSON.stringify({schema:FRAME_OUTPUT_SCHEMA,present,absent,cases})+'\n');
