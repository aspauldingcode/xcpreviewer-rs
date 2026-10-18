import assert from 'node:assert/strict';
import fs from 'node:fs';
import {assess,authorizeSelection} from './stable-guard.mjs';
const ax=fs.readFileSync(new URL('./prior-final-projection.ax.txt',import.meta.url),'utf8');
const value=assess(ax);assert.equal(authorizeSelection(value,value,1,2),65);
const mutants=[ax.replace('menu button (selected) Description: Live','menu button Description: Live'),ax.replace('button Description: Pin Preview, ID: pin','button other'),ax.replace('text Text and interaction','text other'),ax.replace('65 text Text and interaction','65 text Text and interaction\n\t\t\t\t\t\t\t\t\t72 text Text and interaction'),ax.replace('\t\t\t\t\t\t\t\t\t65 text Text and interaction','\t65 text Text and interaction'),ax.replace('59 container','59 container Description: Source Editor')];
for(const bad of mutants){const state=assess(bad);assert.throws(()=>authorizeSelection(state,state,1,2));}
const changed=assess(ax.replace('65 text Text and interaction','75 text Text and interaction'));assert.throws(()=>authorizeSelection(value,changed,1,2),/stale/);
assert.throws(()=>authorizeSelection(value,value,2,2),/deadline/);
console.log(JSON.stringify({passed:true,assertions:9,native_execution:false}));
