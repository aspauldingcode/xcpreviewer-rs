// Official SDK transport/client, owned stdio supervisor; public transport tap only.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const [sdk,runtime,config,inputs,out,supervisor,python]=process.argv.slice(2);
const {Client}=await import(pathToFileURL(path.join(sdk,'node_modules/@modelcontextprotocol/client/dist/index.mjs')));
const {StdioClientTransport}=await import(pathToFileURL(path.join(sdk,'node_modules/@modelcontextprotocol/client/dist/stdio.mjs')));
fs.mkdirSync(out);const records=[];
for(const mode of ['consumer']){
 const root=path.join(out,mode);fs.mkdirSync(root);const source=path.join(root,'owned.swift');
 fs.copyFileSync(path.join(inputs,'0-source.swift'),source);const wire=[];let stderr='';
 const raw=new StdioClientTransport({command:python,args:[supervisor,runtime,config,source,path.join(root,'builds'),path.join(root,'wait.json')],stderr:'pipe',maxBufferSize:32768});
 raw.stderr.on('data',b=>{stderr+=b.toString();assert(Buffer.byteLength(stderr)<=32768)});
 const transport={start:()=>raw.start(),close:()=>raw.close(),send:m=>{wire.push({direction:'send',message:structuredClone(m)});return raw.send(m)},
  set onmessage(fn){raw.onmessage=m=>{wire.push({direction:'receive',message:structuredClone(m)});fn(m)}},
  set onclose(fn){raw.onclose=fn},set onerror(fn){raw.onerror=fn}};
 const client=new Client({name:'owned-official-sdk-control',version:'1'},{capabilities:{},versionNegotiation:{mode:'legacy'}});
 const values=[];
 const {PreviewConsumer}=await import(pathToFileURL(path.join(runtime,'tools/re/reloop/preview_consumer.js')));const samples=[];let interleave=false;
 const request=async(name)=>{const r=await client.callTool({name:'preview_'+name,arguments:{}},{timeout:5000});values.push({name,result:r});return r};
 const consumer=new PreviewConsumer(async p=>{const name=p.name.slice(8);if(name==='frame'&&interleave){interleave=false;fs.copyFileSync(path.join(inputs,'1-source.swift'),source);await request('refresh');}return request(name)});
 const sample=async()=>{const a=await consumer.sample();samples.push({status:a.status,frame:a.frame?{descriptor:a.frame.descriptor,allocationBase64:a.frame.allocation.toString('base64')}:null});return a};
 const tool=async name=>{const r=await client.callTool({name:'preview_'+name,arguments:{}},{timeout:5000});values.push({name,result:r});if(name==='frame'){const value=r.structuredContent;assert.equal(r.content[0].text,value.available?'Frame available.':'No frame available.');return value.frame}return JSON.parse(r.content[0].text)};
 try{
  await client.connect(transport,{timeout:3000});const server=client.getServerVersion();const capabilities=client.getServerCapabilities();
  const tools=await client.listTools({}, {timeout:3000});assert.equal(tools.tools.length,6);
  assert.equal((await sample()).frame,null);
  await tool('start');const first=await sample();assert.equal(first.frame.descriptor.revision,1);
  first.frame.allocation.fill(0);first.status.frame.width=1;assert.equal(consumer.snapshot().frame.descriptor.width,13);await sample();
  interleave=true;const raced=await sample();assert.equal(raced.frame.descriptor.revision,2);assert.equal(raced.frame.descriptor.width,11);
  fs.writeFileSync(source,'Text("consumer-unsupported")');await tool('refresh');assert.equal((await sample()).status.readiness.state,'stale');
  fs.copyFileSync(path.join(inputs,'0-source.swift'),source);await tool('refresh');assert.equal((await sample()).frame.descriptor.revision,3);
  await tool('close');assert.equal((await sample()).status.readiness.state,'closed');assert.equal((await consumer.sample()).frame,null);
  await client.close();
  assert(fs.existsSync(path.join(root,'wait.json')));const wait=JSON.parse(fs.readFileSync(path.join(root,'wait.json')));assert.deepEqual(wait,{timeout:false,code:0});
  const lifecycle=JSON.parse(fs.readFileSync(path.join(root,'builds/session-lifecycle.json')));
  records.push({mode,wire,server,capabilities,tools,values,samples,wait,lifecycle});fs.writeFileSync(path.join(root,'stderr.txt'),stderr);
 }finally{await client.close();fs.writeFileSync(path.join(root,'partial.json'),JSON.stringify({wire,values}));fs.writeFileSync(path.join(root,'stderr.txt'),stderr)}
}
fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({sdkVersion:'2.3.1',negotiation:'explicit legacy',records},null,2)+'\n');
