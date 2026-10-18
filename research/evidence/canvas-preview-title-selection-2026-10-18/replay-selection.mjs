import fs from 'node:fs';
import assert from 'node:assert/strict';
import {assess,authorizeSelection} from './stable-guard.mjs';
const value=assess(fs.readFileSync(new URL('./selection-projection.ax.txt',import.meta.url),'utf8'));
assert.equal(authorizeSelection(value,value,Date.parse('2026-10-18T17:50:00.352Z'),Date.parse('2026-10-18T17:52:00Z')),65);
assert.equal(value.increment,null);
console.log(JSON.stringify({recorded_title_index:65,native_input_qualified:false}));
