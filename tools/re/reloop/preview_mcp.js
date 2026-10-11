'use strict';
// Protocol handler only: caller owns framing, serialization, cancellation and shutdown.
const VERSION='2025-11-25';
const {FRAME_OUTPUT_SCHEMA,frameContent}=require('./preview_frame_contract.js');
const descriptions={start:'Start finite source preview. A rejected build can leave no frame; inspect diagnostics. Starting a closed session fails.',poll:'Read source changes. Rejected edits retain the previous accepted frame; inspect diagnostics.',status:'Read lifecycle, frame descriptor and diagnostics without reading the allocation.',frame:'Read the current accepted allocation. available=false and frame=null before first publication or after close. A rejected edit can retain an older frame; inspect status diagnostics.',close:'Close the session and release its current frame. Repeated close is allowed; restart requires a new server session.'};
const names=['preview_start','preview_poll','preview_status','preview_frame','preview_close'];
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const empty=x=>object(x)&&Object.keys(x).length===0;
class PreviewMcp {
 constructor(session){this.session=session;this.phase='new';this.ids=new Set();}
 async handle(m){
  const validId=x=>typeof x==='string'?(Buffer.byteLength(x)<=128):Number.isSafeInteger(x);
  const error=(id,code,message)=>({jsonrpc:'2.0',...(id===null?{}:{id}),error:{code,message}});
  let bytes;
  try{bytes=Buffer.byteLength(JSON.stringify(m));}catch(_){return error(null,-32600,'Invalid request');}
  if(bytes>4096||!object(m)||m.jsonrpc!=='2.0'||typeof m.method!=='string'||Object.keys(m).some(k=>!['jsonrpc','id','method','params'].includes(k))||('params'in m&&!object(m.params))||('id'in m&&!validId(m.id)))return error(object(m)&&validId(m.id)?m.id:null,-32600,'Invalid request');
  if(!('id'in m)){
   if(m.method==='notifications/initialized'&&this.phase==='negotiated'&&(!('params'in m)||empty(m.params)))this.phase='ready';
   return null;
  }
  const id=m.id,key=typeof id+':'+id;
  if(this.ids.has(key))return error(id,-32600,'Request ID reused');
  if(this.ids.size>=256)return error(id,-32000,'Session request limit');
  this.ids.add(key);
  const reply=result=>({jsonrpc:'2.0',id,result});
  if(m.method==='ping')return reply({});
  if(m.method==='initialize'){
   const p=m.params;
   if(this.phase!=='new')return error(id,-32600,'Already initialized');
   if(!object(p)||typeof p.protocolVersion!=='string'||!object(p.capabilities)||!object(p.clientInfo)||typeof p.clientInfo.name!=='string'||typeof p.clientInfo.version!=='string')return error(id,-32602,'Invalid initialization');
   this.phase='negotiated';
   return reply({protocolVersion:VERSION,capabilities:{tools:{}},serverInfo:{name:'owned-preview-handler',version:'0.2.0'}});
  }
  if(this.phase!=='ready')return error(id,-32000,'Initialization incomplete');
  if(m.method==='tools/list'){
   if('params'in m&&(Object.keys(m.params).some(k=>k!=='_meta')||('_meta'in m.params&&!object(m.params._meta))))return error(id,-32602,'Invalid list parameters');
   return reply({tools:names.map(name=>({name,description:descriptions[name.slice(8)],inputSchema:{type:'object',properties:{},additionalProperties:false},...(name==='preview_frame'?{outputSchema:FRAME_OUTPUT_SCHEMA}:{})}))});
  }
  if(m.method!=='tools/call')return error(id,-32601,'Method not found');
  const p=m.params;
  if(!object(p)||!names.includes(p.name)||Object.keys(p).some(k=>!['name','arguments','_meta'].includes(k))||('arguments'in p&&!empty(p.arguments))||('_meta'in p&&!object(p._meta)))return error(id,-32602,'Invalid tool parameters');
  try{
   let result;
   if(p.name==='preview_start')result=await this.session.start(250,10000);
   else if(p.name==='preview_poll')result=await this.session.poll();
   else if(p.name==='preview_status')result=this.session.status();
   else if(p.name==='preview_close'){await this.session.close();result=this.session.status();}
   else {const f=await this.session.readFrame();if(f&&(!Buffer.isBuffer(f.allocation)||f.allocation.length!==16384))throw Error();result=frameContent(f);}
   const packet=reply({content:[{type:'text',text:p.name==='preview_frame'?(result.available?'Frame available.':'No frame available.'):JSON.stringify(result)}],...(p.name==='preview_frame'?{structuredContent:result}:{})});
   if(Buffer.byteLength(JSON.stringify(packet))>32768)throw Error();
   return packet;
  }catch(_){return reply({content:[{type:'text',text:'Preview operation failed'}],isError:true});}
 }
}
module.exports={PreviewMcp,VERSION};
