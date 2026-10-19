import assert from 'node:assert/strict';import fs from 'node:fs';
import {createSelectionRegistry} from './selection-registry.mjs';
const b=JSON.parse(fs.readFileSync(new URL('./binding.json',import.meta.url))),old='/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b';
const ax=fs.readFileSync(new URL('./prior-final-projection.ax.txt',import.meta.url),'utf8').replaceAll(old,'/private/tmp/callback-ui-access-20261018/workspace');
const config=()=>({session:'a'.repeat(32),workspace:b.projects[0],source_sha256:'b'.repeat(64),stopWall:300,cleanupWall:360});let cases=0;
function make(c=config(),options={}){let t=0,reads=0,clicks=0;const clock=()=>({wall:t,mono:t}),r=createSelectionRegistry(),app={async getAXState(){reads++;if(options.late&&reads===2)t=300;return ax},async click(){clicks++}};const s=r.bind(c,clock,app,b);return {r,s,time:v=>t=v,reads:()=>reads,clicks:()=>clicks,clock,app};}
{const x=make();x.time(15);assert.equal((await x.s.next()).decision,'selection_dispatched');assert.equal(x.clicks(),1);assert.equal(x.s.snapshot().driver.attempts.refresh,0);cases++;}
{const x=make(config(),{late:true});x.time(15);await assert.rejects(x.s.next(),/deadline/);assert.equal(x.clicks(),0);assert.equal(x.s.snapshot().terminal,true);cases++;}
{const x=make();assert.throws(()=>x.r.bind(config(),x.clock,x.app,b),/already bound/);assert.equal(x.reads(),0);cases++;}
{const c=config(),x=make(c);c.stopWall=999999;x.time(300);assert.equal((await x.s.next()).decision,'cleanup');assert.equal(x.clicks(),0);assert.equal(x.reads(),0);cases++;}
{const x=make();const original=[...b.sources];b.sources[0]='/invalid';x.time(15);assert.equal((await x.s.next()).decision,'selection_dispatched');b.sources=original;cases++;}
{const x=make();x.time(14);assert.equal((await x.s.next()).notBeforeWall,15);assert.equal(x.reads(),0);cases++;}
{const r=createSelectionRegistry();assert.throws(()=>r.bind({...config(),cleanupWall:359},()=>({wall:0,mono:0}),{},b),/reserve/);cases++;}
{const r=createSelectionRegistry();assert.throws(()=>r.bind({...config(),workspace:'/private/tmp/DIFFERENT/PreviewLab.xcodeproj'},()=>({wall:0,mono:0}),{},b),/projects binding/);cases++;}
{const r=createSelectionRegistry();assert.throws(()=>r.bind(config(),()=>({wall:0,mono:0}),{},{...b,sources:['/private/tmp/other.swift',b.sources[1]]}),/sources binding/);cases++;}
{const r=createSelectionRegistry();for(const projects of [[b.projects[0],b.projects[0]],[...b.projects].reverse(),[...b.projects,'extra']])assert.throws(()=>r.bind(config(),()=>({wall:0,mono:0}),{},{...b,projects}),/projects binding/);cases++;}
{const r=createSelectionRegistry();assert.throws(()=>r.bind({...config(),workspace:'/private/tmp/a/../PreviewLab.xcodeproj'},()=>({wall:0,mono:0}),{},b),/workspace binding/);cases++;}
console.log(JSON.stringify({cases,native_execution:false,cutoff_unit:'seconds; converted to action milliseconds',scope:'mock registry-driver integration'}));
