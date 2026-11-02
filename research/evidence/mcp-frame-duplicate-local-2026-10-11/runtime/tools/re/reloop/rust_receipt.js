// Strict receipt shape and pinned byte identities for the finite Rust frontend.
'use strict';
const assert=require('node:assert/strict');
function object(value,keys){assert(value&&Object.getPrototypeOf(value)===Object.prototype,'Plain receipt object required');assert.deepEqual(Object.keys(value).sort(),keys.slice().sort(),'Receipt keys mismatch');}
function validateRustReceipt(r,context){
 object(r,['source_sha256','module_sha256','config','rustc_sha256','toolchain_sha256','sources','generated_sha256','cache_hit','target','scope']);
 for(const name of ['source_sha256','module_sha256','rustc_sha256','toolchain_sha256','generated_sha256'])assert(typeof r[name]==='string'&&/^[a-f0-9]{64}$/.test(r[name]),'Receipt digest shape');
 for(const name of ['source_sha256','module_sha256','rustc_sha256','toolchain_sha256','generated_sha256'])assert.equal(r[name],context[name],'Receipt digest identity');
 object(r.config,['width','height','alphas','reverse']);
 for(const name of ['width','height'])assert(Number.isSafeInteger(r.config[name])&&r.config[name]>=1&&r.config[name]<=64,'Receipt extent');
 assert(Array.isArray(r.config.alphas)&&r.config.alphas.length===3&&r.config.alphas.every(x=>Number.isSafeInteger(x)&&x>=0&&x<=8),'Receipt alpha eighths');assert(Number.isSafeInteger(r.config.reverse)&&[0,1].includes(r.config.reverse),'Receipt reverse flag');
 object(r.sources,['contract.rs','wasm-template.rs']);
 for(const name of ['contract.rs','wasm-template.rs'])assert(typeof r.sources[name]==='string'&&/^[a-f0-9]{64}$/.test(r.sources[name])&&r.sources[name]===context.sources[name],'Receipt kernel identity');
 assert.equal(r.cache_hit,false);assert.equal(r.target,'wasm32-wasip1');assert.equal(r.scope,'Finite primary literal expression lowering; not general Swift compilation');return r;
}
module.exports={validateRustReceipt};
