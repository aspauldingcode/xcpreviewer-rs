// Owned v0.2 frame availability and finite allocation contract, not Canvas wire.
'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const hash={type:'string',pattern:'^[a-f0-9]{64}$'};
const integer={type:'integer',minimum:1,maximum:Number.MAX_SAFE_INTEGER};
const descriptor={type:'object',additionalProperties:false,required:['revision','generation','sourceSha256','moduleSha256','allocationSha256','allocationBytes','renderedBytes','width','height','stride','format'],properties:{
 revision:integer,generation:integer,sourceSha256:hash,moduleSha256:hash,allocationSha256:hash,
 allocationBytes:{const:16384},renderedBytes:{type:'integer',minimum:64,maximum:4096},
 width:{type:'integer',minimum:1,maximum:16},height:{type:'integer',minimum:1,maximum:64},stride:{const:64},format:{const:'premultiplied-RGBA8'}}};
const frameSchema={type:'object',additionalProperties:false,required:['descriptor','allocationBase64'],properties:{descriptor,allocationBase64:{type:'string',minLength:21848,maxLength:21848,pattern:'^[A-Za-z0-9+/]{21846}==$'}}};
const FRAME_OUTPUT_SCHEMA={type:'object',additionalProperties:false,required:['available','frame'],properties:{available:{type:'boolean'},frame:{anyOf:[frameSchema,{type:'null'}]}},oneOf:[{properties:{available:{const:true},frame:frameSchema}},{properties:{available:{const:false},frame:{type:'null'}}}]};
const exact=(v,keys)=>assert(v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===keys.slice().sort().join(','),'Invalid frame fields');
function decodeFrameContent(content){
 exact(content,['available','frame']);assert(typeof content.available==='boolean');
 if(!content.available){assert.equal(content.frame,null);return null;}
 const f=content.frame;exact(f,['descriptor','allocationBase64']);const d=f.descriptor;exact(d,descriptor.required);
 for(const k of ['revision','generation'])assert(Number.isSafeInteger(d[k])&&d[k]>=1);
 for(const k of ['sourceSha256','moduleSha256','allocationSha256'])assert(typeof d[k]==='string'&&/^[a-f0-9]{64}$/.test(d[k]));
 assert.equal(d.allocationBytes,16384);assert.equal(d.stride,64);assert.equal(d.format,'premultiplied-RGBA8');
 assert(Number.isSafeInteger(d.width)&&d.width>=1&&d.width<=16&&Number.isSafeInteger(d.height)&&d.height>=1&&d.height<=64);assert.equal(d.renderedBytes,d.height*64);
 assert(typeof f.allocationBase64==='string'&&f.allocationBase64.length===21848&&/^[A-Za-z0-9+/]{21846}==$/.test(f.allocationBase64));
 const allocation=Buffer.from(f.allocationBase64,'base64');assert.equal(allocation.length,16384);assert.equal(allocation.toString('base64'),f.allocationBase64);
 assert.equal(crypto.createHash('sha256').update(allocation).digest('hex'),d.allocationSha256);
 return {descriptor:{...d},allocation};
}
function frameContent(frame){
 const content=frame?{available:true,frame:{descriptor:frame.descriptor,allocationBase64:frame.allocation.toString('base64')}}:{available:false,frame:null};
 decodeFrameContent(content);return content;
}
module.exports={FRAME_OUTPUT_SCHEMA,decodeFrameContent,frameContent};
