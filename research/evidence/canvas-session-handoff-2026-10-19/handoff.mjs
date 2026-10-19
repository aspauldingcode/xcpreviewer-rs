// Research proposal: closure/lease records are trusted inputs, not authenticated here.
export function admitFresh({registry,previous,closure,config,clock,app,binding}){
 const need=(v,m)=>{if(!v)throw Error(m)};
 need(typeof clock==='function'&&app&&app!==previous?.app&&typeof app.getAXState==='function'&&typeof app.click==='function','fresh app/clock');
 need(registry&&Object.isFrozen(registry)&&typeof registry.bind==='function','retained registry');
 need(previous?.closed===true&&previous.control&&previous.app,'closed holder');
 const old=previous.control.snapshot(),context=old?.gate?.context;
 need(old.pending===false&&old.driver?.pending===false&&old.gate?.pending===false,'pending old holder');
 need(closure?.experiment_deadline_closed===true&&closure.cleanup_reconciliation_required===false&&closure.owned_workspace_windows_after===0&&typeof closure.seal_sha256==='string'&&/^[0-9a-f]{64}$/.test(closure.seal_sha256),'closure record');
 need(context&&context.session===closure.nonce&&context.source_sha256===closure.source_sha256&&context.workspace===closure.workspace,'closure context');
 need(previous.config?.session===context.session&&previous.config?.source_sha256===context.source_sha256&&previous.config?.workspace===context.workspace,'holder context');
 need(typeof config?.session==='string'&&config.session!==context.session&&config.workspace===context.workspace&&typeof config.source_sha256==='string'&&config.source_sha256!==context.source_sha256,'fresh context');
 for(const key of ['getAXState','click'])need(Object.getOwnPropertyDescriptor(previous.app,key)?.writable===true,'retirable app wrapper');
 // Old wrappers may look up a global holder dynamically. Retire before replacement.
 const retired=async()=>{throw Error('retired holder')};
 previous.app.getAXState=retired;previous.app.click=retired;
 const c=Object.freeze({...config});let closed=false,AXAttempts=0,lastAX=null;const clickAttempts=[];const holder={config:c,get closed(){return closed},get AXAttempts(){return AXAttempts},get clickAttempts(){return clickAttempts.map(x=>({...x,options:x.options?{...x.options}:undefined}))},get lastAX(){return lastAX}};
 const check=()=>{const t=clock();need(!closed,'holder closed');need(t&&Number.isFinite(t.wall)&&t.wall<c.stopWall,'holder cutoff');};
 holder.app={async getAXState(options){check();need(AXAttempts<16,'holder AX cap');AXAttempts++;const value=await app.getAXState(options);check();lastAX=value;return value},async click(index,options){check();need(clickAttempts.length<2,'holder click cap');clickAttempts.push({index,options:options?{...options}:undefined});const value=await app.click(index,options);check();return value}};
 holder.control=registry.bind(c,clock,holder.app,binding);
 holder.close=()=>{closed=true;};
 return Object.freeze(holder);
}
