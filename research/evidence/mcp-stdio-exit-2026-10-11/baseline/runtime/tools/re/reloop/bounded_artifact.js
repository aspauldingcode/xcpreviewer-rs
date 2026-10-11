// Pin the opened regular file; reject final-component links, FIFOs and read mutation.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
function readArtifact(file,limit=1048576){
 assert(Number.isSafeInteger(limit)&&limit>=1&&limit<=1048576);
 const {O_RDONLY,O_NONBLOCK,O_NOFOLLOW}=fs.constants;
 assert(Number.isInteger(O_NONBLOCK)&&Number.isInteger(O_NOFOLLOW),'Required artifact open flags unavailable');
 const fd=fs.openSync(file,O_RDONLY|O_NONBLOCK|O_NOFOLLOW);
 try{
  const before=fs.fstatSync(fd,{bigint:true});assert(before.isFile()&&before.size>0n&&before.size<=BigInt(limit),'Bounded regular artifact required');
  const bytes=Buffer.alloc(limit+1);let total=0;
  while(total<bytes.length){const n=fs.readSync(fd,bytes,total,bytes.length-total,null);if(!n)break;total+=n;}
  const after=fs.fstatSync(fd,{bigint:true});
  assert(total<=limit&&BigInt(total)===before.size,'Artifact size changed during read');
  for(const k of ['dev','ino','size','mtimeNs','ctimeNs'])assert.equal(after[k],before[k],'Artifact identity changed during read');
  return Buffer.from(bytes.subarray(0,total));
 }finally{fs.closeSync(fd);}
}
module.exports={readArtifact};
