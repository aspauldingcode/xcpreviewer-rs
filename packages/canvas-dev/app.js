const $=id=>document.getElementById(id);
let token,baseHash=null,dirty=false,saving=false,latest=null,displayed=null,pending=null,worker=null,deadline=null,saveTimer=null,closed=false,failedFrame=null,displayError=null;
function diagnostic(message){$('diagnostic').textContent=message||'';$('diagnostic').style.display=message?'block':'none';}
async function request(path,value){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Canvas-Token':token},body:JSON.stringify(value),signal:AbortSignal.timeout(10000)});const body=await r.json();if(!r.ok){const error=Error(body.error||'Request failed');error.status=r.status;throw error;}return body;}
function size(){const scale=Number($('zoom').value)/Number($('canvas').dataset.renderScale||1),c=$('canvas');$('surface').style.width=c.width*scale+'px';$('surface').style.height=c.height*scale+'px';}
async function save(){
 if(saving||!dirty||!baseHash)return;const text=$('source').value;saving=true;
 try{const r=await request('/api/source',{source:text,expected_sha256:baseHash});baseHash=r.source_sha256;dirty=$('source').value!==text;$('save-status').textContent=dirty?'Unsaved edits':'Saved · watching for changes';$('conflict').style.display='none';}
 catch(error){$('save-status').textContent=error.message;if(error.status===409){$('conflict').style.display='block';$('autosave').checked=false;}else diagnostic(error.message);}
 finally{saving=false;if(dirty&&$('autosave').checked)saveTimer=setTimeout(save,400);}
}
function nativePacket(packet){const bytes=new Uint8Array(packet),v=new DataView(packet);if(bytes.length<40||new TextDecoder().decode(bytes.subarray(0,4))!=='XCPV'||v.getUint32(4,true)!==1)throw Error('Invalid capture packet');if(![1,2].includes(v.getFloat64(24,true))||v.getFloat64(32,true)!==0)throw Error('Unsupported capture scale/corner profile');const width=v.getUint32(8,true),height=v.getUint32(12,true),length=v.getUint32(16,true),count=v.getUint32(20,true);if(count!==0||width<1||height<1||width>8192||height>8192||length!==width*height*4||length>32*1024*1024||40+length!==bytes.length)throw Error('Invalid capture extent');const pixels=new Uint8ClampedArray(length);for(let i=0;i<length;i+=4){const a=bytes[40+i+3];pixels[i+3]=a;for(let c=0;c<3;c++)pixels[i+c]=a?Math.floor((bytes[40+i+c]*255+Math.floor(a/2))/a):0;}return{width,height,pixels:pixels.buffer};}
const frameKey=frame=>JSON.stringify([frame.source_sha256,frame.sha256,frame.scale,frame.color_scheme,frame.chrome,frame.title]);
async function paint(frame){
 const key=frameKey(frame);if(pending===key||displayed===key||failedFrame===key)return;
 worker?.terminate();clearTimeout(deadline);pending=key;
 const current=new Worker(frame.kind==='portable'?'/preview-worker.js':'/capture-worker.js');worker=current;
 const fail=message=>{if(worker!==current)return;current.terminate();worker=null;pending=null;failedFrame=key;displayError=message;clearTimeout(deadline);diagnostic(message);};
 deadline=setTimeout(()=>fail('Preview worker exceeded 10 seconds. Last good frame retained.'),10000);
 current.onerror=()=>fail('Preview worker stopped. Last good frame retained.');
 current.onmessage=({data})=>{
  if(worker!==current)return;
  try{if(!data.ok)throw Error(data.error);const value=frame.kind==='portable'?data:nativePacket(data.packet);const pixels=new Uint8ClampedArray(value.pixels);const offscreen=document.createElement('canvas');offscreen.width=value.width;offscreen.height=value.height;offscreen.getContext('2d').putImageData(new ImageData(pixels,value.width,value.height),0,0);
   // Validation and rendering complete before replacing the accepted canvas.
   compose(offscreen,frame);displayed=key;failedFrame=null;displayError=null;pending=null;$('surface').style.display='block';$('empty').style.display='none';$('screenshot').disabled=false;size();current.terminate();worker=null;clearTimeout(deadline);
  }catch(error){fail(error.message);}
 };
 if(frame.kind==='portable')current.postMessage(frame);
 else{try{const r=await fetch('/artifact/'+frame.sha256);if(!r.ok)throw Error('Capture revision unavailable');const input=await r.arrayBuffer();const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',input)),b=>b.toString(16).padStart(2,'0')).join('');if(input.byteLength>64*1024*1024||hash!==frame.sha256)throw Error('Capture integrity check failed');if(worker===current)current.postMessage({input},[input]);}catch(error){fail(error.message);}}
}
async function poll(){
 if(closed)return;
 try{const r=await fetch('/api/session',{signal:AbortSignal.timeout(5000)});if(!r.ok)throw Error('Development server unavailable');latest=await r.json();token=latest.token;syncEnvironment(latest);$('filename').textContent=latest.source_name;
  const first=baseHash===null;if(first&&latest.backend==='swiftui')$('zoom').value='1';
  if(!dirty&&!saving&&latest.source!==null){if(baseHash!==latest.source_sha256){$('source').value=latest.source;highlight();}baseHash=latest.source_sha256;}
  $('backend').textContent=latest.backend==='portable'?'WASM renderer':'Mac SwiftUI → WASM viewer';
  $('compat').textContent=latest.backend==='portable'?'Portable preview · primary-color ZStack expressions, sizes 1–64. General SwiftUI layout, text, state and device behavior are still in development.':'Mac SwiftUI snapshot · public ImageRenderer, no simulator. Builds the selected factory; native interaction and state preservation are not implemented.';
  $('light').dataset.state=latest.state;$('status').textContent=latest.state==='ready'?`Ready · revision ${latest.revision} · ${latest.build_ms} ms`:latest.state==='building'?'Building preview…':latest.state==='error'?'Build failed · last good preview retained':'Starting preview…';
  diagnostic(latest.error||latest.source_error||(latest.frame&&failedFrame===frameKey(latest.frame)?displayError:null));if(latest.frame&&$('follow').checked)await paint(latest.frame);
 }catch(error){$('light').dataset.state='error';$('status').textContent='Disconnected · last good preview retained';diagnostic(error.message);}
 finally{if(!closed)setTimeout(poll,400);}
}
let environmentInitialized=false,environmentBusy=false,environmentQueued=false,environmentSession=null,environmentNeedsSync=false,environmentRetryAt=0;
const systemTheme=matchMedia('(prefers-color-scheme: dark)');
function theme(mode){const resolved=mode==='auto'?(systemTheme.matches?'dark':'light'):mode;document.documentElement.dataset.theme=resolved;return resolved;}
async function environment(){if(!token)return;if(environmentBusy){environmentQueued=true;return;}environmentBusy=true;environmentNeedsSync=false;try{const appearance=$('appearance').value;await request('/api/environment',{...latest.config,appearance,color_scheme:theme(appearance),scale:$('retina').checked?2:1,chrome:$('chrome').checked});localStorage.setItem('canvasAppearance',appearance);environmentRetryAt=0;}catch(error){environmentNeedsSync=true;environmentRetryAt=Date.now()+5000;diagnostic(error.message);}finally{environmentBusy=false;if(environmentQueued){environmentQueued=false;environment();}}}
function syncEnvironment(session){if(!environmentInitialized){environmentInitialized=true;const stored=localStorage.getItem('canvasAppearance');$('appearance').value=['auto','light','dark'].includes(stored)?stored:session.config.appearance;$('retina').checked=session.config.scale===2;$('chrome').checked=session.config.chrome;}if(environmentSession!==session.token){environmentSession=session.token;environmentNeedsSync=true;environmentRetryAt=0;}if(environmentNeedsSync&&!environmentBusy&&Date.now()>=environmentRetryAt){theme($('appearance').value);environment();}}
$('appearance').onchange=environment;$('retina').onchange=environment;$('chrome').onchange=environment;systemTheme.addEventListener('change',()=>{if($('appearance').value==='auto')environment();});
function compose(body,frame){const c=$('canvas'),scale=frame.scale||1,header=frame.chrome?32*scale:0;c.width=body.width;c.height=body.height+header;const ctx=c.getContext('2d');ctx.save();if(header){ctx.beginPath();ctx.roundRect(0,0,c.width,c.height,16*scale);ctx.clip();}ctx.drawImage(body,0,header);if(header){const dark=frame.color_scheme==='dark';ctx.fillStyle=dark?'#303036':'#f6f6f6';ctx.fillRect(0,0,c.width,header);ctx.fillStyle=dark?'#161619':'#d3d3d3';ctx.fillRect(0,header-scale,c.width,scale);for(const x of [16,39,62]){ctx.beginPath();ctx.arc(x*scale,16*scale,6.5*scale,0,Math.PI*2);ctx.fillStyle=dark?'#49494f':'#e6e6e6';ctx.fill();ctx.strokeStyle=dark?'#64646b':'#bdbdbd';ctx.lineWidth=.6*scale;ctx.stroke();}ctx.fillStyle=dark?'#e8e8ec':'#4d4d4d';ctx.font=`600 ${14*scale}px -apple-system, BlinkMacSystemFont, sans-serif`;ctx.textBaseline='middle';ctx.fillText(frame.title||'Preview',84*scale,16*scale);}ctx.restore();c.dataset.artifactSha256=frame.sha256;c.dataset.moduleSha256=frame.kind==='portable'?frame.sha256:'';c.dataset.sourceSha256=frame.source_sha256;c.dataset.renderScale=scale;c.dataset.colorScheme=frame.color_scheme;$('dimensions').textContent=`${c.width/scale} × ${c.height/scale} pt · ${c.width} × ${c.height} px`;}
$('screenshot').onclick=()=>{const c=$('canvas');c.toBlob(blob=>{if(!blob){diagnostic('PNG export failed');return;}const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`canvas-${c.dataset.colorScheme||'light'}@${c.dataset.renderScale}x.png`;link.click();setTimeout(()=>URL.revokeObjectURL(url),10000);},'image/png');};
function highlight(){const text=$('source').value,re=/(\/\*[\s\S]*?\*\/|\/\/[^\n]*|"(?:\\.|[^"\\])*"|\b(?:import|struct|class|enum|func|var|let|some|return|if|else|switch|case|true|false|nil|public|private|static|async|await|throws|try)\b|\b\d+(?:\.\d+)?\b)/g;const fragment=document.createDocumentFragment();let offset=0;for(const match of text.matchAll(re)){fragment.append(document.createTextNode(text.slice(offset,match.index)));const span=document.createElement('span'),v=match[0];span.className='tok-'+(v.startsWith('/')?'comment':v.startsWith('"')?'string':/^\d/.test(v)?'number':'keyword');span.textContent=v;fragment.append(span);offset=match.index+v.length;}fragment.append(document.createTextNode(text.slice(offset)+'\n'));$('highlight').replaceChildren(fragment);syncScroll();}
function syncScroll(){$('highlight').scrollTop=$('source').scrollTop;$('highlight').scrollLeft=$('source').scrollLeft;}$('source').onscroll=syncScroll;
$('source').oninput=()=>{highlight();dirty=true;$('save-status').textContent='Unsaved edits';clearTimeout(saveTimer);if($('autosave').checked)saveTimer=setTimeout(save,450);};
$('source').onkeydown=e=>{if(e.key==='Tab'){e.preventDefault();const t=e.target,start=t.selectionStart,end=t.selectionEnd;t.setRangeText('    ',start,end,'end');t.dispatchEvent(new Event('input'));}};
$('autosave').onchange=()=>{if($('autosave').checked&&dirty)save();};$('save').onclick=save;
$('reload').onclick=()=>{if(latest?.source!==null){$('source').value=latest.source;highlight();baseHash=latest.source_sha256;dirty=false;$('conflict').style.display='none';$('save-status').textContent='Loaded current file';}};
$('refresh').onclick=async()=>{try{if(dirty)await save();await request('/api/refresh',{});if(latest?.frame){displayed=null;failedFrame=null;displayError=null;await paint(latest.frame);}}catch(error){diagnostic(error.message);}};
$('zoom').onchange=size;$('follow').onchange=()=>{if($('follow').checked&&latest?.frame)paint(latest.frame);else{worker?.terminate();worker=null;pending=null;clearTimeout(deadline);}};
window.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='s'){e.preventDefault();save();}});
window.addEventListener('pagehide',()=>{closed=true;worker?.terminate();clearTimeout(deadline);clearTimeout(saveTimer);});poll();
