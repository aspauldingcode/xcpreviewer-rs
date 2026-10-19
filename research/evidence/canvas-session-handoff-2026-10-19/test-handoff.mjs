import assert from 'node:assert/strict';import fs from 'node:fs';
import {admitFresh} from './handoff.mjs';import {createSelectionRegistry} from './selection-registry.mjs';
const binding=JSON.parse(fs.readFileSync(new URL('./binding.json',import.meta.url))),oldPath='/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b';
const ax=fs.readFileSync(new URL('./prior-final-projection.ax.txt',import.meta.url),'utf8').replaceAll(oldPath,'/private/tmp/callback-ui-access-20261018/workspace');
let cases=0;
function setup(){
 let t=0,oldReads=0,newReads=0,clicks=0;const config={session:'a'.repeat(32),source_sha256:'b'.repeat(64),workspace:binding.projects[0],stopWall:300,cleanupWall:360},clock=()=>({wall:t,mono:t});
 const registry=createSelectionRegistry(),previous={config,closed:true,app:{async getAXState(){oldReads++;return ax},async click(){clicks++}}};previous.control=registry.bind(config,clock,previous.app,binding);
 const closure={nonce:config.session,source_sha256:config.source_sha256,workspace:config.workspace,experiment_deadline_closed:true,cleanup_reconciliation_required:false,owned_workspace_windows_after:0,seal_sha256:'c'.repeat(64)};
 const fresh={...config,session:'d'.repeat(32),source_sha256:'e'.repeat(64)};const app={async getAXState(){newReads++;return ax},async click(){clicks++}};
 return {registry,previous,closure,config:fresh,clock,app,binding,time:x=>t=x,counts:()=>({oldReads,newReads,clicks})};
}
{const s=setup(),h=admitFresh(s);assert.throws(()=>s.registry.bind(s.previous.config,s.clock,{},binding),/already bound/);await assert.rejects(s.previous.app.getAXState(),/retired/);await assert.rejects(s.previous.app.click(1),/retired/);assert.deepEqual(s.counts(),{oldReads:0,newReads:0,clicks:0});s.time(15);assert.equal((await h.control.next()).decision,'selection_dispatched');assert.equal(h.clickAttempts.length,1);assert.equal(s.counts().clicks,1);assert.equal(s.counts().oldReads,0);cases++;}
{const s=setup();s.previous.closed=false;assert.throws(()=>admitFresh(s),/closed holder/);assert.equal(s.counts().oldReads,0);cases++;}
{for(const [key,val] of [['experiment_deadline_closed',false],['cleanup_reconciliation_required',true],['owned_workspace_windows_after',1],['owned_workspace_windows_after',false],['seal_sha256','bad']]){const s=setup();s.closure[key]=val;assert.throws(()=>admitFresh(s),/closure record/);}cases++;}
{for(const key of ['nonce','source_sha256','workspace']){const s=setup();s.closure[key]='wrong';assert.throws(()=>admitFresh(s),/closure context/);}cases++;}
{const s=setup();s.previous.config={...s.previous.config,session:'wrong'};assert.throws(()=>admitFresh(s),/holder context/);cases++;}
{const s=setup();s.config.session=s.previous.config.session;assert.throws(()=>admitFresh(s),/fresh context/);cases++;}
{const s=setup();s.config.workspace='/private/tmp/other/PreviewLab.xcodeproj';assert.throws(()=>admitFresh(s),/fresh context/);cases++;}
{const s=setup();Object.freeze(s.previous.app);assert.throws(()=>admitFresh(s),/retirable/);cases++;}
{const s=setup(),h=admitFresh(s);h.close();await assert.rejects(h.app.getAXState(),/closed/);await assert.rejects(h.app.click(1),/closed/);assert.deepEqual(s.counts(),{oldReads:0,newReads:0,clicks:0});cases++;}
{const s=setup(),h=admitFresh(s);s.config.stopWall=999999;s.time(300);await assert.rejects(h.app.getAXState(),/cutoff/);assert.equal(s.counts().newReads,0);cases++;}
{let release;const wait=new Promise(r=>release=r),s=setup();s.app.getAXState=async()=>wait;const h=admitFresh(s);const first=h.app.getAXState();h.close();release(ax);await assert.rejects(first,/closed/);assert.equal(s.counts().clicks,0);cases++;}
{const s=setup(),h=admitFresh(s);await h.app.click(11,{clickCount:2});await h.app.click(77);await assert.rejects(h.app.click(77),/cap/);assert.equal(s.counts().clicks,2);cases++;}
{const s=setup(),h=admitFresh(s);for(let i=0;i<16;i++)await h.app.getAXState();await assert.rejects(h.app.getAXState(),/cap/);assert.equal(s.counts().newReads,16);cases++;}
{const s=setup();s.previous.control={snapshot(){return {pending:true}}};assert.throws(()=>admitFresh(s),/pending/);cases++;}
{const s=setup();s.app=s.previous.app;assert.throws(()=>admitFresh(s),/fresh app/);cases++;}
{const s=setup(),h=admitFresh(s);h.close();assert.throws(()=>{h.closed=false},TypeError);await assert.rejects(h.app.getAXState(),/closed/);cases++;}
{const s=setup(),h=admitFresh(s);await h.app.click(1,{clickCount:2});h.clickAttempts.length=0;await h.app.click(2);await assert.rejects(h.app.click(3),/cap/);assert.equal(s.counts().clicks,2);cases++;}
{const s=setup();s.binding={...binding,projects:['wrong','wrong']};assert.throws(()=>admitFresh(s),/projects binding/);await assert.rejects(s.previous.app.getAXState(),/retired/);assert.equal(s.counts().newReads,0);cases++;}
{let release;const wait=new Promise(r=>release=r),s=setup();s.app.click=async()=>wait;const h=admitFresh(s),first=h.app.click(11,{clickCount:2});h.close();release('unverified-result');await assert.rejects(first,/closed/);assert.equal(h.clickAttempts.length,1);cases++;}
{let release;const wait=new Promise(r=>release=r),s=setup();s.app.click=async()=>wait;const h=admitFresh(s),first=h.app.click(11);s.time(300);release('unverified-result');await assert.rejects(first,/cutoff/);assert.equal(h.clickAttempts.length,1);cases++;}
console.log(JSON.stringify({cases,native_execution:false,retained_registry_old_nonce_rejected:true,retired_old_wrapper_zero_reads:true,scope:'Trusted closure record and mock app; no authentication/ownership proof'}));
