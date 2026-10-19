import assert from 'node:assert/strict';import {createReadiness} from './local-readiness.mjs';
function setup(){let time=0,calls=0;const clock=()=>({wall:1000+time,mono:time});const gate=createReadiness({session:'owned-nonce',stopWall:1240,cleanupWall:1300},clock);return {gate,at:t=>time=t,calls:()=>calls,app:{async getAXState(){calls++;return 'AX'}}};}
let cases=0;
{
 const s=setup();assert.equal((await s.gate.sample(s.app,x=>x)).decision,'independent_work');assert.equal(s.calls(),0);
 for(const t of [15,45,90,180]){s.at(t);assert.equal((await s.gate.sample(s.app,x=>x)).decision,'observed')}
 s.at(181);assert.equal((await s.gate.sample(s.app,x=>x)).decision,'cleanup');assert.equal(s.calls(),4);cases++;
}
{
 const s=setup();s.at(180);await s.gate.sample(s.app,x=>x);assert.equal((await s.gate.sample(s.app,x=>x)).decision,'independent_work');s.at(210);await s.gate.sample(s.app,x=>x);assert.equal((await s.gate.sample(s.app,x=>x)).decision,'cleanup');assert.equal(s.calls(),2);cases++;
}
{
 const s=setup();s.at(15);assert.equal((await s.gate.sample(s.app,()=>{throw Error('busy')})).outcome,'busy');const x=s.gate.snapshot();x.history.length=0;s.at(16);assert.equal((await s.gate.sample(s.app,x=>x)).decision,'independent_work');cases++;
}
{
 const s=setup();s.at(15);await assert.rejects(s.gate.sample(s.app,()=>{throw Error('ownership')}),/ownership/);s.at(45);assert.equal((await s.gate.sample(s.app,x=>x)).decision,'cleanup');assert.equal(s.calls(),1);cases++;
}
{
 const s=setup();s.at(240);assert.equal((await s.gate.sample(s.app,x=>x)).decision,'cleanup');assert.equal(s.calls(),0);cases++;
}
{
 const s=setup();s.at(15);let release;const wait=new Promise(r=>release=r);const first=s.gate.sample({async getAXState(){await wait;return 'AX'}},x=>x);await assert.rejects(s.gate.sample(s.app,x=>x),/pending/);release();await first;cases++;
}
{
 const s=setup();s.at(15);await assert.rejects(s.gate.sample({async getAXState(){s.at(240);return 'AX'}},x=>x),/late/);assert.equal(s.gate.snapshot().failed,true);cases++;
}
{
 const s=setup();s.at(15);await s.gate.sample(s.app,x=>x);s.at(14);await assert.rejects(s.gate.sample(s.app,x=>x),/clock/);cases++;
}
{
 let first=true;const g=createReadiness({session:'owned',stopWall:1240,cleanupWall:1300},()=>first?(first=false,{wall:1000,mono:0}):{wall:1020,mono:1});await assert.rejects(g.sample({},x=>x),/divergence/);cases++;
}
{
 const initial={wall:1000,mono:0};let first=true;const g=createReadiness({session:'owned',stopWall:1240,cleanupWall:1300},()=>first?(first=false,initial):{wall:1015,mono:15});initial.wall=900;initial.mono=-100;assert.equal((await g.sample({async getAXState(){return 'AX'}},x=>x)).decision,'observed');assert.deepEqual(g.snapshot().start,{wall:1000,mono:0});cases++;
}
console.log(JSON.stringify({cases,native_execution:false,scope:'trusted injected clock/mocks; actual CUA clock and one-instance lifecycle still require review'}));
