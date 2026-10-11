'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {LiveWasmHost}=require('../reloop/live_wasm_host.js');
const dir=process.argv[2], baselineOnly=process.argv[3]==='before';
const fixture=path.resolve(__dirname,'../../../research/evidence/live-wasm-swap-2026-10-10');
const rows=JSON.parse(fs.readFileSync(path.join(fixture,'fixtures.json')));
const bytes=fs.readFileSync(path.join(fixture,'0-view.wasm')),frame=fs.readFileSync(path.join(fixture,'0-allocation.raw'));
function loopModule(){
 const section=(id,v)=>[id,v.length,...v],name=s=>[s.length,...Buffer.from(s)];
 const bodies=[[0,0x41,0x80,0x80,1,0x0b],[0,0x41,0,0x0b],[0,0x03,0x40,0x0c,0,0x0b,0x41,0,0x0b]];
 return Buffer.from([0,97,115,109,1,0,0,0,...section(1,[2,0x60,0,1,0x7f,0x60,1,0x7f,1,0x7f]),...section(3,[3,0,0,1]),...section(5,[1,1,2,2]),...section(7,[4,...name('capacity'),0,0,...name('pixels'),0,1,...name('render'),0,2,...name('memory'),2,0]),...section(10,[3,...bodies.flatMap(b=>[b.length,...b])])]);
}
const propose=(host,module=bytes)=>host.propose(module,frame,rows[0].config.width,rows[0].config.height,rows[0].stride,500);
(async()=>{
 const host=new LiveWasmHost();let settled=false,error;
 const first=await propose(host),baseline=host.snapshot();
 const pending=propose(host,loopModule()).then(()=>{settled=true;},e=>{settled=true;error=String(e);});
 await assert.rejects(propose(host),/already active/);
 assert.deepEqual(host.snapshot(),baseline);
 const start=performance.now();await host.close();const closeMs=performance.now()-start,settledAtClose=settled;
 const status=host.status?host.status():null;
 await pending;assert.equal(host.snapshot(),null);await host.close();await assert.rejects(propose(host));
 if(!baselineOnly){assert(settledAtClose,'close returned before proposal settlement');assert.equal(status.liveWorkers,0);assert.equal(status.busy,false);assert.equal(status.closed,true);assert.match(error,/exited|closed|cancel/i);}
 const extra=[];
 if(!baselineOnly){
  for(const mode of ['empty-valid-proposal','live-read','active-valid-proposal']){
   const h=new LiveWasmHost();if(mode!=='empty-valid-proposal')await propose(h);
   let finished=false,operationError;
   const operation=(mode==='live-read'?h.verifyLive():propose(h)).then(()=>{finished=true;},e=>{finished=true;operationError=String(e);});
   await Promise.all([h.close(),h.close()]);await operation;
   assert(finished);assert(operationError);assert.equal(h.snapshot(),null);
   assert.deepEqual(h.status(),{liveWorkers:0,busy:false,closed:true,revision:mode==='empty-valid-proposal'?0:1});
   extra.push({case:mode,error:operationError,status:h.status(),settled_at_close:finished});
  }
 }
 fs.writeFileSync(path.join(dir,baselineOnly?'before-fix.json':'after-fix.json'),JSON.stringify({settled_at_close:settledAtClose,close_ms:closeMs,proposal_error:error,status_at_close:status,last_good_before_close:true,compared_bytes:16384,after_close_snapshot:null,extra_controls:extra},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
