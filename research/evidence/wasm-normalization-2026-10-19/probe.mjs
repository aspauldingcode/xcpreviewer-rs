// Source-only arithmetic conformance harness; no renderer, Canvas or UI APIs.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('.',import.meta.url)),raw=fs.readFileSync(root+'probe.wasm');
const need=(v,s)=>{if(!v)throw Error(s)};
need(raw.subarray(0,8).equals(Buffer.from([0,97,115,109,1,0,0,0])),'header');
let offset=8;const sections=[];
while(offset<raw.length){const id=raw[offset++];let n=0,shift=0,b;do{need(offset<raw.length&&shift<35,'section length');b=raw[offset++];n+=(b&127)*2**shift;shift+=7}while(b&128);need(Number.isSafeInteger(n)&&offset+n<=raw.length,'section bounds');sections.push(id);offset+=n}
need(JSON.stringify(sections)==='[1,3,7,10]','no imports/memory/start/custom sections');
need(WebAssembly.validate(raw),'WASM validation');const module=new WebAssembly.Module(raw),imports=WebAssembly.Module.imports(module),exports=WebAssembly.Module.exports(module);
need(imports.length===0&&JSON.stringify(exports)===JSON.stringify([{name:'multiplyBits',kind:'function'},{name:'divideBits',kind:'function'}]),'module shape');
const instance=new WebAssembly.Instance(module,{});const scratch=new DataView(new ArrayBuffer(4));let calls=0;
function bits(method,code){
 if(typeof code!=='number'||!Number.isInteger(code)||code<0||code>255)throw Error('byte domain');
 calls++;
 if(method==='wasm-multiply')return instance.exports.multiplyBits(code)>>>0;
 if(method==='wasm-divide')return instance.exports.divideBits(code)>>>0;
 const value=method==='js-multiply'?Math.fround(Math.fround(code)*Math.fround(1/255)):Math.fround(code/255);
 scratch.setFloat32(0,value,true);return scratch.getUint32(0,true);
}
const invalid=[];
for(const [label,value] of [['negative',-1],['large',256],['fraction',.5],['nonfinite',NaN],['boolean',true]]){const before=calls;let rejected=false;try{bits('wasm-multiply',value)}catch{rejected=true}need(rejected&&calls===before,'invalid domain dispatch');invalid.push({label,rejected,dispatch_delta:calls-before})}
const rows=[];
for(const method of ['wasm-multiply','wasm-divide','js-multiply','js-divide']){
 const bytes=Buffer.alloc(16384,0xa5),view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 for(let y=0;y<3;y++)for(let x=0;x<256;x++){for(let c=0;c<3;c++)view.setUint32(y*4160+x*16+c*4,bits(method,(x+c*85)&255),true);view.setUint32(y*4160+x*16+12,0x3f800000,true)}
 const file=method+'.raw';fs.writeFileSync(root+'owned-output/'+file,bytes,{flag:'wx'});rows.push({method,file,allocation_bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});
}
console.log(JSON.stringify({pid:process.pid,environment:{node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch},module_sha256:crypto.createHash('sha256').update(raw).digest('hex'),module_bytes:raw.length,sections,imports,exports,invalid_inputs:invalid,scalar_dispatches:calls,rows,native_UI_execution:false,product_integration:false,second_runtime_verified:false,non_Apple_OS_verified:false}));
