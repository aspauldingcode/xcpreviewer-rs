'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {validateRustReceipt}=require('../reloop/rust_receipt.js');
const data=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});const copy=x=>JSON.parse(JSON.stringify(x));
const context=r=>Object.fromEntries([...['source_sha256','module_sha256','rustc_sha256','toolchain_sha256','generated_sha256'].map(k=>[k,r[k]]),['sources',copy(r.sources)]]);
const valid=data.builds.map(x=>({receipt:copy(x.receipt),context:context(x.receipt)}));for(const row of valid)validateRustReceipt(row.receipt,row.context);
const base=valid[0].receipt,mutants=[];
function mutation(name,change){let r=copy(base);r=change(r)||r;let error=null;try{validateRustReceipt(r,context(base));}catch(e){error=String(e);}assert(error,'Mutant must reject: '+name);mutants.push({case:name,receipt:r,context:context(base),error});}
for(const key of Object.keys(base))mutation('missing-'+key,r=>{delete r[key];});
mutation('extra-root',r=>{r.extra=1;});mutation('array-root',()=>[]);
mutation('source-pin',r=>{r.source_sha256='0'.repeat(64);});mutation('module-digest-shape',r=>{r.module_sha256='A'.repeat(64);});
for(const v of [0,65,1.5,'13'])mutation('width-'+JSON.stringify(v),r=>{r.config.width=v;});
for(const v of [0,65])mutation('height-'+v,r=>{r.config.height=v;});
mutation('alpha-count',r=>{r.config.alphas.pop();});for(const v of [-1,9,0.5,true])mutation('alpha-'+v,r=>{r.config.alphas[0]=v;});
mutation('reverse-string',r=>{r.config.reverse='false';});mutation('reverse-boolean',r=>{r.config.reverse=false;});mutation('config-extra',r=>{r.config.extra=0;});mutation('sources-extra',r=>{r.sources.extra='0'.repeat(64);});mutation('cache-true',r=>{r.cache_hit=true;});mutation('target-wrong',r=>{r.target='wasm32-unknown-unknown';});mutation('scope-empty',r=>{r.scope='';});mutation('compiler-pin',r=>{r.rustc_sha256='0'.repeat(64);});mutation('toolchain-pin',r=>{r.toolchain_sha256='0'.repeat(64);});assert.equal(mutants.length,34);
fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({valid,mutants,scope:'Strict schema and pinned receipt identities from actual finite Rust builds; no universal source or native Canvas claim'},null,2)+'\n');
