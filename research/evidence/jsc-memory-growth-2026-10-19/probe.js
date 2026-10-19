// Public JSContext counterpart; preserves full engine export descriptors without asserting unmeasured keys.
(function(){
const need=(v,s)=>{if(!v)throw Error(s)};
const bytes=new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0, 1, 11, 2, 96, 2, 127, 127, 0, 96, 1, 127, 1, 127, 3, 3, 2, 0, 1, 5, 4, 1, 1, 1, 2, 7, 26, 3, 6, 109, 101, 109, 111, 114, 121, 2, 0, 6, 115, 116, 111, 114, 101, 56, 0, 0, 4, 103, 114, 111, 119, 0, 1, 10, 18, 2, 9, 0, 32, 0, 32, 1, 58, 0, 0, 11, 6, 0, 32, 0, 64, 0, 11]);
need(WebAssembly.validate(bytes),'module validation');
const module=new WebAssembly.Module(bytes),imports=WebAssembly.Module.imports(module),engine_exports=WebAssembly.Module.exports(module),exports=engine_exports.map(e=>({name:e.name,kind:e.kind}));
need(imports.length===0&&JSON.stringify(exports)===JSON.stringify([{name:'memory',kind:'memory'},{name:'store8',kind:'function'},{name:'grow',kind:'function'}]),'owned module shape');
const instance=new WebAssembly.Instance(module,{}),{memory,store8,grow}=instance.exports;
let view=new Uint8Array(memory.buffer);need(view.length===65536,'initial pages');view.fill(0xa5);
for(let y=0;y<5;y++)for(let x=0;x<17;x++)for(let c=0;c<4;c++)view[y*96+x*4+c]=(x*7+y*11+c*31)&255;
store8(0,17);
const rows=[],events=[];
function save(stage){const raw=new Uint8Array(memory.buffer),file=stage+'.raw';rows.push({stage,file,bytes:raw.length,hex:Array.from(raw,b=>b.toString(16).padStart(2,'0')).join('')})}
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
return JSON.stringify({module_sha256:'970468fb9b02b07bd628c530877571db3d2ca614f73e8498b6fdd40455b3c0c6',module_bytes:bytes.length,imports,exports,engine_exports,rows,events,browser_execution:false,native_canvas_evidence:false,product_integration:false});
})()
