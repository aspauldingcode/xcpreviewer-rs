'use strict';
const fs=require('node:fs'),path=require('node:path');
const {rustSourceBuilder}=require('../reloop/rust_source_builder.js');
const {SourceRevisionHost}=require('../reloop/source_revision_host.js');
const evidence=path.resolve(process.argv[2]),cfg=JSON.parse(fs.readFileSync(path.join(evidence,'config.json'))),source=fs.readFileSync(path.join(cfg.input,'0-source.swift'));
cfg.oracle=()=>fs.readFileSync(path.join(evidence,'0-expected.raw'));
const builder=rustSourceBuilder(cfg),host=new SourceRevisionHost();
(async()=>{try{const ticket=host.begin(source),result=await builder(source,{signal:new AbortController().signal}),frame=await host.submit(ticket,result.build,result.expected);fs.writeFileSync(path.join(evidence,'0-frame.raw'),frame.frame);await host.close();fs.writeFileSync(path.join(evidence,'result.json'),JSON.stringify({records:builder.records(),failures:builder.failures(),status:host.status()},null,2)+'\n');}catch(error){fs.writeFileSync(path.join(evidence,'retained-failure.json'),JSON.stringify({error:String(error),records:builder.records(),failures:builder.failures()},null,2)+'\n');throw error;}finally{await host.close();fs.writeFileSync(path.join(evidence,'closure.json'),JSON.stringify(host.status())+'\n');}})().catch(error=>{console.error(error);process.exitCode=1;});
