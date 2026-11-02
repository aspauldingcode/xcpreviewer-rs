// Official SDK transport/client, owned stdio supervisor; public transport tap only.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const [sdk,runtime,config,inputs,out,supervisor,python]=process.argv.slice(2);
const {Client}=await import(pathToFileURL(path.join(sdk,'node_modules/@modelcontextprotocol/client/dist/index.mjs')));
const {StdioClientTransport}=await import(pathToFileURL(path.join(sdk,'node_modules/@modelcontextprotocol/client/dist/stdio.mjs')));
fs.mkdirSync(out);const records=[];
for(const mode of ['edits','eof']){
 const root=path.join(out,mode);fs.mkdirSync(root);const source=path.join(root,'owned.swift');
 fs.copyFileSync(path.join(inputs,'0-source.swift'),source);const wire=[];let stderr='';
 const raw=new StdioClientTransport({command:python,args:[supervisor,runtime,config,source,path.join(root,'builds'),path.join(root,'wait.json')],stderr:'pipe',maxBufferSize:32768});
 raw.stderr.on('data',b=>{stderr+=b.toString();assert(Buffer.byteLength(stderr)<=32768)});
 const transport={start:()=>raw.start(),close:()=>raw.close(),send:m=>{wire.push({direction:'send',message:structuredClone(m)});return raw.send(m)},
  set onmessage(fn){raw.onmessage=m=>{wire.push({direction:'receive',message:structuredClone(m)});fn(m)}},
  set onclose(fn){raw.onclose=fn},set onerror(fn){raw.onerror=fn}};
 const client=new Client({name:'owned-official-sdk-control',version:'1'},{capabilities:{},versionNegotiation:{mode:'legacy'}});
 const values=[];
 const tool=async name=>{const r=await client.callTool({name:'preview_'+name,arguments:{}},{timeout:5000});values.push({name,result:r});return JSON.parse(r.content[0].text)};
 try{
  await client.connect(transport,{timeout:3000});const server=client.getServerVersion();const capabilities=client.getServerCapabilities();
  const tools=await client.listTools({}, {timeout:3000});assert.equal(tools.tools.length,5);
  await tool('start');await tool('frame');
  if(mode==='edits'){
   fs.copyFileSync(path.join(inputs,'1-source.swift'),source);await tool('poll');await tool('frame');
   fs.writeFileSync(source,'Text("unsupported")');assert.equal((await tool('poll')).diagnostics.lastFailure.kind,'rejected');await tool('frame');
   fs.copyFileSync(path.join(inputs,'2-source.swift'),source);await tool('poll');await tool('frame');
   assert.equal((await tool('close')).lifecycle.loopClosed,true);
   assert.equal(await tool('frame'),null);
   const r=await client.callTool({name:'preview_start',arguments:{}},{timeout:1000});assert.equal(r.isError,true);values.push({name:'closed-start',result:r});
  }
  await client.close();
  assert(fs.existsSync(path.join(root,'wait.json')));const wait=JSON.parse(fs.readFileSync(path.join(root,'wait.json')));assert.deepEqual(wait,{timeout:false,code:0});
  const lifecycle=JSON.parse(fs.readFileSync(path.join(root,'builds/session-lifecycle.json')));
  records.push({mode,wire,server,capabilities,tools,values,wait,lifecycle});fs.writeFileSync(path.join(root,'stderr.txt'),stderr);
 }finally{await client.close()}
}
fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({sdkVersion:'2.3.1',negotiation:'explicit legacy',records},null,2)+'\n');
