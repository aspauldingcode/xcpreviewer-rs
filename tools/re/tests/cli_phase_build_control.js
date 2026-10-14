'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const {SourceRevisionHost}=require('../reloop/source_revision_host.js');
const evidence=path.resolve(process.argv[2]),cfg=JSON.parse(fs.readFileSync(path.join(evidence,'config.json'))),sources=[0,2].map(index=>fs.readFileSync(path.join(cfg.input,index+'-source.swift')));
cfg.oracle=source=>fs.readFileSync(path.join(evidence,sources[0].equals(source)?'0-expected.raw':'2-expected.raw'));
const builder=rustSourceBuilder(cfg),host=new SourceRevisionHost();
(async()=>{try{for(let index=0;index<2;index++){const ticket=host.begin(sources[index]),result=await builder(sources[index],{signal:new AbortController().signal});const frame=await host.submit(ticket,result.build,result.expected);fs.writeFileSync(path.join(evidence,index+'-frame.raw'),frame.frame);}await host.close();fs.writeFileSync(path.join(evidence,'result.json'),JSON.stringify({records:builder.records(),failures:builder.failures(),status:host.status()},null,2)+'\n');assert.equal(builder.records().length,2);assert.equal(builder.failures().length,0);}catch(error){fs.writeFileSync(path.join(evidence,'retained-failure.json'),JSON.stringify({error:String(error),records:builder.records(),failures:builder.failures()},null,2)+'\n');throw error;}finally{await host.close();fs.writeFileSync(path.join(evidence,'closure.json'),JSON.stringify(host.status())+'\n');}})().catch(error=>{console.error(error);process.exitCode=1;});
