// The portable preview actually executes in this worker; it is not a served PNG.
const digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
self.onmessage=async({data:frame})=>{try{
 const response=await fetch('/artifact/'+frame.sha256);if(!response.ok)throw Error('Renderer revision unavailable');
 const bytes=await response.arrayBuffer();if(bytes.byteLength>1048576||await digest(bytes)!==frame.sha256)throw Error('Renderer integrity check failed');
 const module=await WebAssembly.compile(bytes);if(WebAssembly.Module.imports(module).length)throw Error('Import-free renderer required');
 const exports=WebAssembly.Module.exports(module).map(e=>e.name+':'+e.kind).sort().join(',');
 if(exports!=='capacity:function,memory:memory,pixels:function,render:function')throw Error('Unexpected renderer interface');
 const e=(await WebAssembly.instantiate(module,{})).exports;
 if(!Number.isInteger(frame.width)||!Number.isInteger(frame.height)||frame.width<1||frame.width>64||frame.height<1||frame.height>64||frame.stride<frame.width*4||frame.stride>256)throw Error('Unsupported preview dimensions');
 if(e.memory.buffer.byteLength!==131072||e.capacity()!==16384)throw Error('Unexpected renderer allocation');
 const pointer=e.pixels();if(pointer<0||pointer+16384>e.memory.buffer.byteLength)throw Error('Invalid pixel allocation');
 const allocation=new Uint8Array(e.memory.buffer,pointer,16384);allocation.fill(0xc3);
 if(e.render(frame.stride)!==frame.stride*frame.height||e.memory.buffer.byteLength!==131072)throw Error('Invalid render extent');
 if(await digest(allocation)!==frame.allocation_sha256)throw Error('Browser output differs from validated build');
 const pixels=new Uint8ClampedArray(frame.width*frame.height*4);
 for(let y=0;y<frame.height;y++)for(let x=0;x<frame.width;x++){
  const at=y*frame.stride+x*4,to=(y*frame.width+x)*4,a=allocation[at+3];pixels[to+3]=a;
  for(let c=0;c<3;c++)pixels[to+c]=a?Math.floor((allocation[at+c]*255+Math.floor(a/2))/a):0;
 }
 const scale=frame.scale||1;if(![1,2].includes(scale))throw Error('Unsupported scale');
 const output=new Uint8ClampedArray(frame.width*frame.height*scale*scale*4);
 for(let y=0;y<frame.height*scale;y++)for(let x=0;x<frame.width*scale;x++){const at=(Math.floor(y/scale)*frame.width+Math.floor(x/scale))*4;output.set(pixels.subarray(at,at+4),(y*frame.width*scale+x)*4);}
 self.postMessage({ok:true,width:frame.width*scale,height:frame.height*scale,pixels:output.buffer},[output.buffer]);
 }catch(error){self.postMessage({ok:false,error:String(error.message||error)})}};
