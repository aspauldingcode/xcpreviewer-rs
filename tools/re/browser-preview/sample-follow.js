// Original polling policy; native Canvas refresh scheduling is not implied.
export function createSampleFollower({read, apply, failed, schedule=setTimeout, cancel=clearTimeout, interval=1000}) {
 let active=false, epoch=0, timer=null, seen=null, lastError=null;
 async function tick(current) {
  try {
   const {buffer,fingerprint}=await read();
   if(!active||epoch!==current)return;
   const recovered=lastError!==null;lastError=null;
   if(fingerprint!==seen||recovered){seen=fingerprint;apply(buffer);}
  } catch(error) {
   if(active&&epoch===current&&error.message!==lastError){lastError=error.message;failed(error);}
  } finally {
   if(active&&epoch===current)timer=schedule(()=>tick(current),interval);
  }
 }
 function stop(){active=false;epoch++;cancel(timer);timer=null;read.abort?.();}
 return {start(){stop();active=true;seen=null;lastError=null;void tick(epoch);},stop};
}

export function createSampleReader(fetcher=fetch) {
 let controller=null;
 const read=async()=>{
  const own=new AbortController();controller=own;
  const timeout=setTimeout(()=>own.abort(),5000);
  try {
   const response=await fetcher('./sample.bplist',{cache:'no-store',signal:own.signal});
   if(!response.ok)throw Error('Sample unavailable');
   const buffer=await response.arrayBuffer();
   if(buffer.byteLength>64*1024*1024)throw Error('Preview file exceeds 64 MiB');
   const digest=await crypto.subtle.digest('SHA-256',buffer);
   return {buffer,fingerprint:Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('')};
  } finally {clearTimeout(timeout);if(controller===own)controller=null;}
 };
 read.abort=()=>controller?.abort();
 return read;
}
