'use strict';
const assert=require('node:assert/strict');
const {accepted,admissible,sinkBuffers}=require('./owned_build_probe.js');
const m={retained_logical:0,scratch_logical:0,allocated:0,files:0,directories:0};
const record={emergencyClosed:false,signal:'SIGKILL',report:{kind:'complete',drained:true,failure:null,
 target_code:0,remaining_observed:0,tracked:2,observations:4,scope:'finite owned observation'}};
assert(accepted(record,m));
for(const change of [{drained:false},{remaining_observed:1},{target_code:65},{failure:'deadline'}])
 assert(!accepted({...record,report:{...record.report,...change}},m));
assert(!accepted({...record,emergencyClosed:true},m));
assert(!accepted({...record,signal:null},m));
assert(!accepted({...record,report:null},m));
assert(!admissible({...m,retained_logical:512*1024**2}));
assert(!admissible({...m,allocated:512*1024**2}));
assert(!admissible({...m,files:-1}));
const expanded={stdout:Buffer.alloc(1048576,255).toString('utf8'),stderr:''};
assert.equal(Buffer.byteLength(expanded.stdout),3145728);
assert.throws(()=>sinkBuffers(expanded,{},2097152),/Encoded sink reserve/);
assert.equal(sinkBuffers(expanded,{}).stdout.length,3145728);
assert.throws(()=>sinkBuffers({}, {text:'x'.repeat(65536)}),/Report reserve/);
process.stdout.write('15 guarded admission and encoded-sink controls pass\n');
