// Owned workflow policy: current publication and historical failures are distinct.
'use strict';
const assert=require('node:assert/strict');
function previewReadiness(status){
 assert(status&&status.schemaVersion===1&&status.lifecycle&&status.diagnostics);
 const l=status.lifecycle,f=status.frame,last=status.diagnostics.latest;
 assert(typeof l.closed==='boolean'&&typeof l.loopClosed==='boolean'&&typeof l.building==='boolean'&&typeof l.busy==='boolean');
 if(f)assert(Number.isSafeInteger(f.revision)&&f.revision>0&&Number.isSafeInteger(f.generation)&&f.generation>0);
 const summary=(state,message)=>({state,frameRevision:f?f.revision:null,message});
 if(l.closed||l.loopClosed)return summary('closed','Preview closed.');
 if(l.building||l.busy)return summary(f?'updating':'building',f?'Updating preview; last frame retained.':'Building preview.');
 if(last&&['rejected','invalid-source','unavailable-source'].includes(last.kind)){
  const cause={rejected:'Source rejected.', 'invalid-source':'Source invalid.', 'unavailable-source':'Source unavailable.'}[last.kind];
  return summary(f?'stale':'failed',f?'Last frame retained. '+cause+' Edit source to retry.':cause+' Edit source to retry.');
 }
 if(f){assert(last&&last.kind==='published'&&last.generation===f.generation,'Publication/readiness mismatch');return summary('ready','Preview ready.');}
 assert(!last||last.kind==='observed','Unexpected empty preview state');return summary('waiting','Preview waiting for source.');
}
module.exports={previewReadiness};
