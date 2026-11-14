async page=>{
 // Actual browser and app code; simulated session rotation and failed HTTP response.
 // Routes intercept every API request: no source or user server settings are changed.
 const state={token:'fixture-session-a',source:'import SwiftUI\n// disposable reconnect fixture\n',source_sha256:'fixture-source-a',source_name:'Fixture.swift',backend:'swiftui',state:'ready',revision:0,frame:null,config:{appearance:'auto',color_scheme:'light',scale:2,chrome:true,width:600,height:400}};
 const calls=[];let rejectNext=false;
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;
  if(path==='/api/session')return route.fulfill({json:state});
  if(path==='/api/environment'){
   const payload=request.postDataJSON(),token=request.headers()['x-canvas-token'];
   if(rejectNext){rejectNext=false;calls.push({token,payload,rejected:true,at:Date.now()});return route.fulfill({status:503,json:{error:'Deliberate temporary environment failure'}});}
   if(token!==state.token)throw Error('Stale token used for environment synchronization');
   state.config={...payload};calls.push({token,payload,rejected:false,at:Date.now()});return route.fulfill({json:{config:state.config}});
  }
  throw Error('Unexpected API request: '+path);
 });
 try{
  await page.addInitScript(()=>{if(location.protocol==='http:')localStorage.removeItem('canvasAppearance');});
  await page.goto('http://127.0.0.1:57945');
  await page.waitForFunction(()=>document.querySelector('#filename').textContent==='Fixture.swift');
  await page.getByLabel('Auto save',{exact:true}).uncheck();
  const unsaved='import SwiftUI\n// preserve my unsaved text\n';await page.getByRole('textbox',{name:'Swift source'}).fill(unsaved);
  await page.getByLabel('Appearance',{exact:true}).selectOption('dark');
  await page.getByLabel('@2x Retina').uncheck();await page.getByLabel('Titlebar (view only)').uncheck();
  await page.waitForTimeout(700);
  if(state.config.appearance!=='dark'||state.config.scale!==1||state.config.chrome!==false)throw Error('Initial controls were not synchronized');
  const started=Date.now();state.token='fixture-session-b';state.config={appearance:'auto',color_scheme:'light',scale:2,chrome:true,width:600,height:400};rejectNext=true;
  // Wait for the application's bounded 5-second retry, not a test-issued request.
  await page.waitForFunction(()=>document.querySelector('#diagnostic').textContent.includes('Deliberate temporary environment failure'));
  const limit=Date.now()+10000;while(Date.now()<limit&&!calls.some(c=>c.token==='fixture-session-b'&&!c.rejected))await page.waitForTimeout(100);
  const retry=calls.find(c=>c.token==='fixture-session-b'&&!c.rejected),failure=calls.find(c=>c.token==='fixture-session-b'&&c.rejected);
  if(!retry||!failure||retry.at-failure.at<5000)throw Error('Bounded environment retry did not complete');
  if(state.config.appearance!=='dark'||state.config.color_scheme!=='dark'||state.config.scale!==1||state.config.chrome!==false)throw Error('Reconnect lost preferences');
  if(await page.getByRole('textbox',{name:'Swift source'}).inputValue()!==unsaved)throw Error('Reconnect overwrote unsaved source');
  return{classification:'actual Chromium/app controls; simulated session/HTTP fault, no native producer',reconnectedPreferences:state.config,unsavedTextPreserved:true,rejectedRequests:1,retryDelayMs:retry.at-failure.at,totalReconnectMs:Date.now()-started,sourceWrites:0};
 }finally{await page.goto('about:blank');await page.unroute('**/api/**');}
}
