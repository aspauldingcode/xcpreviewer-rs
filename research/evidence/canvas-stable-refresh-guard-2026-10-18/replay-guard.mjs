import fs from 'node:fs';
import assert from 'node:assert/strict';
import {assess,authorize} from './stable-guard.mjs';
const before=assess(fs.readFileSync(new URL('./before-projection.ax.txt',import.meta.url),'utf8'));
assert.equal(authorize(before,before,'refresh',Date.parse('2026-10-18T17:39:34.314Z'),Date.parse('2026-10-18T17:41:00Z')),61);
assert.throws(()=>assess(fs.readFileSync(new URL('./busy-projection.ax.txt',import.meta.url),'utf8')),/busy/);
const final=assess(fs.readFileSync(new URL('./final-projection.ax.txt',import.meta.url),'utf8'));
assert.equal(final.increment,null);assert.equal(final.refresh,null);
console.log(JSON.stringify({recorded_refresh_index:61,busy_rejected:true,final_input_qualified:false}));
