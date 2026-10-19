import {createReadiness} from './local-readiness.mjs';
export function createSessionRegistry(){
 const sessions=new Map();
 return Object.freeze({bind(config,clock){
  const {session,workspace,source_sha256,stopWall,cleanupWall}=config;
  if(typeof session!=='string'||!/^[0-9a-f]{32}$/.test(session)||typeof workspace!=='string'||!workspace.startsWith('/private/tmp/')||!workspace.endsWith('/PreviewLab.xcodeproj')||typeof source_sha256!=='string'||!/^[0-9a-f]{64}$/.test(source_sha256))throw Error('owned session configuration');
  if(sessions.has(session))throw Error('session already bound');
  const context=Object.freeze({session,workspace,source_sha256,stopWall,cleanupWall}),gate=createReadiness(context,clock);
  const bound=Object.freeze({sample:(app,assess)=>gate.sample(app,assess),snapshot:()=>({...gate.snapshot(),context:{...context}})});sessions.set(session,bound);return bound;
 }});
}
