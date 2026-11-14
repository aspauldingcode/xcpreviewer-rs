async page=>{
 // Only run on a disposable copy of examples/canvas-swiftui.swift: this test edits its file.
 const assert=(v,m)=>{if(!v)throw Error(m);};const editor=page.getByRole('textbox',{name:'Swift source'});
 await page.waitForFunction(()=>document.querySelector('#canvas').dataset.artifactSha256);
 await page.getByLabel('Canvas appearance',{exact:true}).selectOption('light');
 await page.waitForFunction(()=>document.querySelector('#canvas').dataset.colorScheme==='light');
 const read=()=>page.evaluate(async()=>{const c=document.querySelector('#canvas'),p=c.getContext('2d').getImageData(0,0,c.width,c.height).data;return{artifact:c.dataset.artifactSha256,source:c.dataset.sourceSha256,width:c.width,height:c.height,pixel:Array.from(c.getContext('2d').getImageData(10,80,1,1).data),readbackSha256:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',p)),b=>b.toString(16).padStart(2,'0')).join('')};});
 const original=await editor.inputValue(),initial=await read();assert(original.includes('.background(Color.white)'),'Requires disposable sample fixture');assert(initial.width===1200&&initial.height===800,'Expected true @2x backing');
 let output;
 try{
 const changed=original.replace('.background(Color.white)','.background(Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1))');const start=Date.now();await editor.fill(changed);
 await page.waitForFunction(old=>document.querySelector('#canvas').dataset.artifactSha256!==old,initial.artifact);
 const edited=await read();assert(JSON.stringify(edited.pixel)==='[255,0,0,255]','Source edit did not reach Canvas');
 const editToPaintMs=Date.now()-start;
 await editor.fill('import SwiftUI\n@MainActor func makePreview() -> some View { MissingPreviewType() }');await page.getByRole('status').filter({hasText:'Build failed'}).waitFor();const failed=await read();assert(failed.readbackSha256===edited.readbackSha256,'Compile failure changed last good pixels');
 await editor.fill(original);await page.waitForFunction(old=>document.querySelector('#canvas').dataset.artifactSha256!==old,edited.artifact);const recovered=await read();assert(JSON.stringify(recovered.pixel)==='[255,255,255,255]','Recovery failed');
 await page.getByLabel('Titlebar (view only)').uncheck();await page.waitForFunction(()=>document.querySelector('#canvas').height===800&&document.querySelector('#canvas').getContext('2d').getImageData(0,0,1,1).data[3]===255);
 const noChrome=await read();assert(noChrome.pixel.every(v=>v===255),'Chrome-off content incorrect');
 output={initial,edited,editToPaintMs,compileFailureRetainedFullReadback:true,recovered,titlebarOffExercised:true};
 }finally{if(await editor.inputValue()!==original){await editor.fill(original);await page.getByRole('button',{name:'Save',exact:true}).click();}}
 return output;
}
