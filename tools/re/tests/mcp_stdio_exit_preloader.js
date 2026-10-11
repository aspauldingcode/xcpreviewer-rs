const Module=require('node:module'),crypto=require('node:crypto');const original=Module._load;
const section=(id,v)=>[id,v.length,...v],name=s=>[s.length,...Buffer.from(s)];
function moduleBytes(hang){
 const bodies=[[0,0x41,0x80,0x80,1,0x0b],hang?[0,0x23,0,0x41,1,0x6a,0x24,0,0x23,0,0x41,3,0x4b,0x04,0x40,0x03,0x40,0x0c,0,0x0b,0x0b,0x41,0,0x0b]:[0,0x41,0,0x0b],[0,0x20,0,0x41,4,0x4f,0x20,0,0x41,0x80,2,0x4d,0x71,0x04,0x7f,...(hang?[]:[0,1,2,3].flatMap(i=>[0x41,i,0x41,0xf7,0,0x3a,0,0])),0x20,0,0x05,0x41,0,0x0b,0x0b]];
 return Buffer.from([0,97,115,109,1,0,0,0,...section(1,[2,0x60,0,1,0x7f,0x60,1,0x7f,1,0x7f]),...section(3,[3,0,0,1]),...section(5,[1,1,2,2]),...section(6,[1,0x7f,1,0x41,0,0x0b]),...section(7,[4,...name('capacity'),0,0,...name('pixels'),0,1,...name('render'),0,2,...name('memory'),2,0]),...section(10,[3,...bodies.flatMap(b=>[b.length,...b])])]);
}


// Owned test-only dependency injection; actual CLI/channel/session execute. No Rust/native compiler claim.
Module._load=function(request,parent,isMain){
 if(parent?.filename.endsWith('/preview_mcp_stdio.js')&&request==='./reloop/rust_source_builder.js')return {rustSourceBuilder:()=>{const b=async bytes=>{const module=moduleBytes(false),expected=Buffer.alloc(16384,0xc3);expected.fill(0x77,0,4);return {build:{module,moduleSha256:crypto.createHash('sha256').update(module).digest('hex'),sourceSha256:crypto.createHash('sha256').update(bytes).digest('hex'),config:{width:1,height:1},stride:64},expected};};b.records=()=>[];b.failures=()=>[];return b;}};
 const value=original.apply(this,arguments);
 if(parent?.filename.endsWith('/preview_mcp_stdio.js')&&request==='./reloop/preview_session.js'&&process.env.OWNED_CLEANUP_MODE==='failed')return {PreviewSession:class extends value.PreviewSession{async close(){await super.close();throw Error('private injected close failure');}}};
 return value;
};
