import assert from 'node:assert/strict';import {createSessionRegistry} from './session-registry.mjs';
const config={session:'a'.repeat(32),workspace:'/private/tmp/owned/workspace/PreviewLab.xcodeproj',source_sha256:'b'.repeat(64),stopWall:1240,cleanupWall:1300};let t=0;const clock=()=>({wall:1000+t,mono:t}),registry=createSessionRegistry(),gate=registry.bind(config,clock);
assert.throws(()=>registry.bind(config,clock),/already bound/);
const snap=gate.snapshot();snap.context.source_sha256='x';config.source_sha256='c'.repeat(64);assert.equal(gate.snapshot().context.source_sha256,'b'.repeat(64));
let calls=0;const app={async getAXState(){calls++;return 'AX'}};t=15;await gate.sample(app,x=>x);assert.throws(()=>registry.bind({...config,source_sha256:'d'.repeat(64)},clock),/already bound/);t=16;assert.equal((await gate.sample(app,x=>x)).decision,'independent_work');assert.equal(calls,1);
for(const bad of [{...config,session:''},{...config,workspace:'/Users/user/Wawona.xcodeproj'},{...config,source_sha256:'x'}])assert.throws(()=>registry.bind(bad,clock),/configuration/);
console.log(JSON.stringify({assertions:8,native_execution:false,scope:'one registry instance; trusted clock/config; no filesystem authentication'}));
