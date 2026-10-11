'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {LiveWasmHost} = require('../reloop/live_wasm_host.js');
const dir = process.argv[2];
const config = JSON.parse(fs.readFileSync(path.join(dir, 'fixtures.json')));
const modules = [0,1].map(i => fs.readFileSync(path.join(dir, i + '-view.wasm')));
const frames = [0,1].map(i => fs.readFileSync(path.join(dir, i + '-allocation.raw')));
function ownedFault(loop) {
  const section = (id, values) => [id, values.length, ...values];
  const name = text => [text.length, ...Buffer.from(text)];
  const bodies = [[0,0x41,0x80,0x80,1,0x0b], [0,0x41,0,0x0b],
    loop ? [0,0x03,0x40,0x0c,0,0x0b,0x41,0,0x0b] : [0,0,0x0b]];
  return Buffer.from([0,97,115,109,1,0,0,0,
    ...section(1,[2,0x60,0,1,0x7f,0x60,1,0x7f,1,0x7f]),
    ...section(3,[3,0,0,1]), ...section(5,[1,1,2,2]),
    ...section(7,[4,...name('capacity'),0,0,...name('pixels'),0,1,...name('render'),0,2,...name('memory'),2,0]),
    ...section(10,[3,...bodies.flatMap(b=>[b.length,...b])])]);
}
(async () => {
  const host = new LiveWasmHost();
  const receipts = [];
  const propose = (i,bytes=modules[i],frame=frames[i],timeout=1500) => host.propose(bytes,frame,config[i].config.width,config[i].config.height,config[i].stride,timeout);
  try {
    await assert.rejects(propose(0,Buffer.from([0]))); assert.equal(host.snapshot(),null);
    const first = await propose(0); assert.deepEqual(first.frame,frames[0]);
    assert.equal(host.status().liveWorkers,1);
    first.frame.fill(0); assert.deepEqual(host.snapshot().frame,frames[0]);
    const baseline = host.snapshot();
    const cases = [['malformed',Buffer.from([0]),frames[0]],['trap',ownedFault(false),frames[0]],
      ['deadline',ownedFault(true),frames[0]],['pixel',modules[0],Buffer.from(frames[0])],
      ['padding',modules[0],Buffer.from(frames[0])],['tail',modules[0],Buffer.from(frames[0])]];
    cases[3][2][0]^=1; cases[4][2][68]^=1; cases[5][2][16383]^=1;
    for (const [name,bytes,prediction] of cases) {
      let error;
      try { await propose(0,bytes,prediction,name==='deadline'?200:1500); }
      catch(e) { error=String(e); }
      assert(error,'Fault proposal unexpectedly accepted: '+name);
      if(name==='trap') assert.match(error,/unreachable/);
      if(name==='deadline') assert.match(error,/deadline/);
      assert.deepEqual(host.snapshot(),baseline);
      assert.deepEqual(await host.verifyLive(),baseline);
      assert.equal(host.status().liveWorkers,1);
      receipts.push({case:name,error,retained_revision:baseline.revision,compared_bytes:16384,live_instance_verified:true});
    }
    const second=await propose(1);assert.equal(second.revision,2);assert.notEqual(second.token,baseline.token);
    assert.deepEqual(second.frame,frames[1]);assert.deepEqual(await host.verifyLive(),second);
    assert.equal(host.status().liveWorkers,1);
    await host.close();assert.equal(host.snapshot(),null);await assert.rejects(propose(0));
    assert.equal(host.status().liveWorkers,0);
    fs.writeFileSync(path.join(dir,'control-result.json'),JSON.stringify({node:process.version,v8:process.versions.v8,platform:process.platform,architecture:process.arch,accepted:2,faults:receipts,full_comparison_bytes:16384*8,scope:'Owned swap policy; no native Canvas sequencing or SwiftUI state migration'},null,2)+'\n');
  } finally { await host.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
