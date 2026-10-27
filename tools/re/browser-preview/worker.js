// Bounded stdin/stdout-only WASI host for the owned canvas-frame executable.
// No filesystem, sockets, environment variables, or arbitrary import stubs.
self.onmessage=async({data})=>{try{
 const input=new Uint8Array(data.input);if(input.length>64*1024*1024)throw Error('Preview file exceeds 64 MiB');
 let memory,position=0,total=0,diagnostic=0;const chunks=[],errors=[];
 const range=(pointer,length)=>{pointer>>>=0;length>>>=0;if(pointer+length>memory.buffer.byteLength)throw Error('Invalid WebAssembly memory range');return new Uint8Array(memory.buffer,pointer,length)};
 const view=()=>new DataView(memory.buffer);
 class Exit extends Error{constructor(code){super('Preview exit '+code);this.code=code}}
 const wasi={
  environ_sizes_get:(count,size)=>{view().setUint32(count,0,true);view().setUint32(size,0,true);return 0},environ_get:()=>0,
  fd_read:(fd,iov,count,result)=>{if(fd!==0)return 8;count>>>=0;if(count>1024)return 28;let n=0;for(let i=0;i<count;i++){const p=view().getUint32(iov+i*8,true),size=view().getUint32(iov+i*8+4,true),buffer=range(p,size),amount=Math.min(size,input.length-position);buffer.set(input.subarray(position,position+amount));position+=amount;n+=amount;}view().setUint32(result,n,true);return 0},
  fd_write:(fd,iov,count,result)=>{if(fd!==1&&fd!==2)return 8;count>>>=0;if(count>1024)return 28;let n=0;for(let i=0;i<count;i++){const p=view().getUint32(iov+i*8,true),size=view().getUint32(iov+i*8+4,true),bytes=range(p,size);if(fd===1){total+=size;if(total>70*1024*1024)throw Error('Preview output exceeds limit');chunks.push(bytes.slice())}else{diagnostic+=size;if(diagnostic>65536)throw Error('Preview diagnostic exceeds limit');errors.push(bytes.slice())}n+=size;}view().setUint32(result,n,true);return 0},
  proc_exit:code=>{throw new Exit(code)}
 };
 const response=await fetch('./canvas-frame.wasm');if(!response.ok)throw Error('Preview engine unavailable');const module=await WebAssembly.compile(await response.arrayBuffer());
 for(const item of WebAssembly.Module.imports(module)){if(item.module!=='wasi_snapshot_preview1'||item.kind!=='function'||!Object.hasOwn(wasi,item.name))throw Error('Unsupported preview engine import: '+item.name)}
 const instance=await WebAssembly.instantiate(module,{wasi_snapshot_preview1:wasi});memory=instance.exports.memory;
 try{instance.exports._start()}catch(error){if(!(error instanceof Exit)||error.code!==0){const text=errors.map(x=>new TextDecoder().decode(x)).join('').trim();throw Error(text||error.message)}}
 const packet=new Uint8Array(total);let offset=0;for(const chunk of chunks){packet.set(chunk,offset);offset+=chunk.length;}
 self.postMessage({ok:true,packet:packet.buffer},[packet.buffer]);
 }catch(error){self.postMessage({ok:false,error:String(error.message||error)})}};
