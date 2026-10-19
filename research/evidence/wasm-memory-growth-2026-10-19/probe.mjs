// Owned non-browser V8/WebAssembly memory lifecycle assay; no UI or product API.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('.',import.meta.url));
const need=(v,s)=>{if(!v)throw Error(s)};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=fs.readFileSync(root+'probe.wasm');
need(WebAssembly.validate(bytes),'module validation');
const module=new WebAssembly.Module(bytes),imports=WebAssembly.Module.imports(module),exports=WebAssembly.Module.exports(module);
need(imports.length===0&&JSON.stringify(exports)===JSON.stringify([{name:'memory',kind:'memory'},{name:'store8',kind:'function'},{name:'grow',kind:'function'}]),'owned module shape');
const instance=new WebAssembly.Instance(module,{}),{memory,store8,grow}=instance.exports;
let view=new Uint8Array(memory.buffer);need(view.length===65536,'initial pages');view.fill(0xa5);
for(let y=0;y<5;y++)for(let x=0;x<17;x++)for(let c=0;c<4;c++)view[y*96+x*4+c]=(x*7+y*11+c*31)&255;
store8(0,17);
const rows=[],events=[];
function save(stage){const raw=Buffer.from(new Uint8Array(memory.buffer));const file=stage+'.raw';fs.writeFileSync(root+'owned-output/'+file,raw,{flag:'wx'});rows.push({stage,file,bytes:raw.length,sha256:hash(raw)})}
function detached(oldBuffer,oldView,oldData,newBuffer,offset){
 let error=null;try{oldData.getUint8(0)}catch(e){error=e.name}
 const before=new Uint8Array(newBuffer)[offset];oldView[offset]=221;
 return {buffer_changed:oldBuffer!==newBuffer,old_buffer_bytes:oldBuffer.byteLength,old_view_bytes:oldView.byteLength,data_view_error:error,stale_read_undefined:oldView[offset]===undefined,stale_write_affected_current:new Uint8Array(newBuffer)[offset]!==before};
}
save('initial');
let oldBuffer=memory.buffer,oldView=view,oldData=new DataView(oldBuffer);
const zeroReturn=memory.grow(0);let newBuffer=memory.buffer;
events.push({phase:'zero-grow',return_value:zeroReturn,new_buffer_bytes:newBuffer.byteLength,...detached(oldBuffer,oldView,oldData,newBuffer,1)});
view=new Uint8Array(newBuffer);store8(1,34);save('zero-grow');
oldBuffer=memory.buffer;oldView=view;oldData=new DataView(oldBuffer);
const positiveReturn=grow(1);newBuffer=memory.buffer;
events.push({phase:'positive-grow',return_value:positiveReturn,new_buffer_bytes:newBuffer.byteLength,...detached(oldBuffer,oldView,oldData,newBuffer,1)});
view=new Uint8Array(newBuffer);store8(65539,51);save('positive-grow');
oldBuffer=memory.buffer;oldView=view;let error=null;
try{memory.grow(1)}catch(e){error=e.name}
events.push({phase:'js-failed-grow',error,buffer_same:memory.buffer===oldBuffer,view_bytes:oldView.byteLength,new_buffer_bytes:memory.buffer.byteLength});
store8(2,68);save('js-failed-grow');
oldBuffer=memory.buffer;oldView=view;const failedReturn=grow(1);
events.push({phase:'wasm-failed-grow',return_value:failedReturn,buffer_same:memory.buffer===oldBuffer,view_bytes:oldView.byteLength,new_buffer_bytes:memory.buffer.byteLength});
store8(3,85);save('wasm-failed-grow');
console.log(JSON.stringify({pid:process.pid,environment:{node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch,executable:process.execPath},module_sha256:hash(bytes),module_bytes:bytes.length,imports,exports,rows,events,browser_execution:false,native_canvas_evidence:false,product_integration:false}));
