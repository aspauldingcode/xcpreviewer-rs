import assert from 'node:assert/strict';import fs from 'node:fs';import {assessReport} from './normalized-guard.mjs';import {guardedClick} from './action.mjs';
const root='/private/tmp/callback-ui-access-20261018/workspace',old='/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b',b=JSON.parse(fs.readFileSync(new URL('./binding.json',import.meta.url))),ax=fs.readFileSync(new URL('./prior-final-projection.ax.txt',import.meta.url),'utf8').replaceAll(old,root),previous=assessReport(ax,b);
for(const [text,prior,now,stop,expected] of [[ax,previous,1,2,1],[ax,previous,2,2,0],[ax,{signature:'stale'},1,2,0],[ax+'\n\t65 duplicate',previous,1,2,0],['x'.repeat(262145),previous,1,2,0]]){
 const calls=[];const app={async getAXState(){calls.push('AX');return text},async click(i){calls.push(i)}};
 try{await guardedClick(app,prior,b,'selection',stop,()=>now);assert.equal(expected,1)}catch(e){assert.equal(expected,0)}
 assert.equal(calls.filter(x=>typeof x==='number').length,expected);if(expected)assert.deepEqual(calls,['AX',65,'AX']);
}
console.log(JSON.stringify({cases:5,scope:'synthetic same-call wrapper; no native authority'}));
