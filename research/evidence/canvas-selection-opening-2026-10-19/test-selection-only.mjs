import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createReadiness} from './local-readiness.mjs';
import {createDriver} from './session-driver.mjs';
import {createSelectionOnly} from './selection-only.mjs';
import {assessReport} from './normalized-guard.mjs';
const b=JSON.parse(fs.readFileSync(new URL('./binding.json',import.meta.url)));
const old='/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b';
const ax=fs.readFileSync(new URL('./prior-final-projection.ax.txt',import.meta.url),'utf8').replaceAll(old,'/private/tmp/callback-ui-access-20261018/workspace');
const paused=ax.replace('text Text and interaction','text Other preview');
const busy=ax.replace(/text Value: [^\n]*ID: Activity Text/,'text Value: Indexing, ID: Activity Text');
assert.equal(assessReport(paused,b).selection,null);assert.ok(Number.isInteger(assessReport(ax,b).selection));
let cases=0;
function make(sequence=[ax,ax,ax],options={}){
 let t=0,reads=0,clicks=[];const queue=[...sequence];
 const gate=createReadiness({session:'test',stopWall:300,cleanupWall:360},()=>({wall:t,mono:t}));
 const app={async getAXState(){reads++;const next=queue.shift();if(next instanceof Error)throw next;if(typeof next==='function')return next();return next??ax},async click(i){clicks.push(i);if(options.clickError)throw Error('click outcome unknown')}};
 const driver=createDriver({gate,app,binding:b,stopMs:300000,clock:()=>t*1000});
 const session=createSelectionOnly({driver,assess:x=>assessReport(x,b)});
 return {session,driver,gate,time:v=>t=v,reads:()=>reads,clicks};
}
// Readiness clock/cutoffs are seconds; action deadline/clock are milliseconds.
{
 const s=make();s.time(15);assert.deepEqual(await s.session.next(),{decision:'selection_dispatched',effect_verified:false});assert.deepEqual(s.clicks,[assessReport(ax,b).selection]);assert.equal(s.reads(),3);assert.equal(s.session.snapshot().terminal,true);assert.equal(s.driver.snapshot().attempts.refresh,0);await assert.rejects(s.session.next(),/terminal/);cases++;
}
{
 const s=make([paused,ax,ax,ax]);s.time(15);assert.equal((await s.session.next()).decision,'wait');assert.equal(s.reads(),1);assert.equal(s.clicks.length,0);s.time(45);assert.equal((await s.session.next()).decision,'selection_dispatched');assert.equal(s.clicks.length,1);cases++;
}
{
 const s=make([busy,ax,ax,ax]);s.time(15);assert.equal((await s.session.next()).outcome,'busy');assert.equal(s.session.snapshot().terminal,false);s.time(45);assert.equal((await s.session.next()).decision,'selection_dispatched');cases++;
}
{
 const s=make([ax,busy]);s.time(15);await assert.rejects(s.session.next(),/busy/);assert.equal(s.clicks.length,0);assert.equal(s.driver.snapshot().terminal,true);const n=s.reads();s.time(90);await assert.rejects(s.session.next(),/terminal/);assert.equal(s.reads(),n);cases++;
}
{
 const s=make([ax,ax.replace('text Primary layers','text Changed layers')]);s.time(15);await assert.rejects(s.session.next(),/stale/);assert.equal(s.clicks.length,0);cases++;
}
{
 const s=make([ax,ax,Error('post-click observation lost')]);s.time(15);await assert.rejects(s.session.next(),/post-click/);assert.equal(s.clicks.length,1);assert.equal(s.driver.snapshot().dispatch_attempts.selection,1);assert.equal(s.session.snapshot().terminal,true);cases++;
}
{
 const s=make([ax,ax],{clickError:true});s.time(15);await assert.rejects(s.session.next(),/outcome unknown/);assert.equal(s.clicks.length,1);assert.equal(s.session.snapshot().terminal,true);cases++;
}
{
 const s=make();s.time(14);assert.equal((await s.session.next()).decision,'independent_work');assert.equal(s.reads(),0);assert.equal(s.clicks.length,0);cases++;
}
{
 const s=make([paused,paused,paused,paused]);for(const t of [15,45,90,180]){s.time(t);assert.equal((await s.session.next()).decision,'wait');}s.time(181);assert.equal((await s.session.next()).decision,'cleanup');assert.equal(s.reads(),4);assert.equal(s.clicks.length,0);await assert.rejects(s.session.next(),/terminal/);cases++;
}
{
 let release;const held=new Promise(r=>release=r);const s=make([()=>held]);s.time(15);const first=s.session.next();await assert.rejects(s.session.next(),/concurrent/);release(ax);await assert.rejects(first,/terminal/);assert.equal(s.clicks.length,0);assert.equal(s.driver.snapshot().terminal,true);cases++;
}
{
 const s=make([ax,()=>{s.time(300);return ax}]);s.time(15);await assert.rejects(s.session.next(),/deadline/);assert.equal(s.clicks.length,0);cases++;
}
{
 const s=make([Error('AX unavailable')]);s.time(15);await assert.rejects(s.session.next(),/AX unavailable/);assert.equal(s.session.snapshot().terminal,true);assert.equal(s.clicks.length,0);cases++;
}
{
 let release;const held=new Promise(r=>release=r),s=make([ax,()=>held]);s.time(15);const first=s.session.next();while(s.reads()<2)await Promise.resolve();await assert.rejects(s.session.next(),/concurrent/);release(ax);await assert.rejects(first,/terminal/);assert.equal(s.clicks.length,0);assert.equal(s.driver.snapshot().terminal,true);cases++;
}
console.log(JSON.stringify({cases,native_execution:false,refresh_dispatches:0,scope:'Owned mock app/readiness/action integration; no native authority'}));
