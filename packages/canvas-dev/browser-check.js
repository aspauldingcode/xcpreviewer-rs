async page=>{
 // Open a freshly started native sample session before invoking this check.
await page.waitForFunction(()=>document.querySelector('#canvas').dataset.renderScale==='2');
 const read=()=>page.evaluate(()=>{const c=document.querySelector('#canvas');return{width:c.width,height:c.height,scale:c.dataset.renderScale,scheme:c.dataset.colorScheme,cssWidth:c.getBoundingClientRect().width,bodyPixel:Array.from(c.getContext('2d').getImageData(10,80,1,1).data),highlightTokens:document.querySelectorAll('#highlight span').length,theme:document.documentElement.dataset.theme};});
 const initial=await read();if(initial.width!==1200||initial.height!==800||initial.highlightTokens<10)throw Error(JSON.stringify(initial));
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Screenshot PNG'}).click();const download=await downloadPromise;await download.saveAs('/private/tmp/libre-canvas-project@2x.png');
 await page.getByLabel('Canvas appearance',{exact:true}).selectOption('dark');await page.waitForFunction(()=>document.querySelector('#canvas').dataset.colorScheme==='dark');const dark=await read();
 await page.getByLabel('@2x Retina').uncheck();await page.waitForFunction(()=>document.querySelector('#canvas').dataset.renderScale==='1');const one=await read();if(one.width!==600||one.height!==400)throw Error('Wrong 1x dimensions');
 await page.getByLabel('Canvas appearance',{exact:true}).selectOption('auto');await page.emulateMedia({colorScheme:'light'});await page.waitForFunction(()=>document.querySelector('#canvas').dataset.colorScheme==='light');
 await page.emulateMedia({colorScheme:'dark'});await page.waitForFunction(()=>document.querySelector('#canvas').dataset.colorScheme==='dark');const auto=await read();
 await page.getByLabel('@2x Retina').check();await page.waitForFunction(()=>document.querySelector('#canvas').dataset.renderScale==='2');
 await page.screenshot({path:'/private/tmp/libre-canvas-editor-dark.png'});
 return{initial,dark,one,auto,screenshot:download.suggestedFilename(),autoFollowedSystem:true,sourceEditsPerformed:false};
}
