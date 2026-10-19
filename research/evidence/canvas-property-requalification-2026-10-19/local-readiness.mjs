// Offline proposal: instantiate once per fixed owned session, inside the UI caller.
// The outer controller lease still owns exclusive backend access and cleanup.
export function createReadiness(config,clock){
 const {session,stopWall,cleanupWall}=config;
 if(typeof session!=='string'||!session||typeof clock!=='function')throw Error('configuration');
 const initial=clock(),start=Object.freeze({wall:initial?.wall,mono:initial?.mono});const finite=x=>typeof x==='number'&&Number.isFinite(x);
 if(![start.wall,start.mono,stopWall,cleanupWall].every(finite)||!(start.wall<stopWall&&stopWall+60<=cleanupWall))throw Error('clock/reserve');
 const offsets=[15,45,90,180],history=[];let last=0,pending=false,failed=false;
 function now(){const t=clock();if(!finite(t.wall)||!finite(t.mono))throw Error('clock');const elapsed=t.mono-start.mono;if(elapsed<last||Math.abs(t.wall-start.wall-elapsed)>5)throw Error('clock divergence/regression');last=elapsed;return {...t,elapsed};}
 return Object.freeze({
  async sample(app,assess){
   if(pending)throw Error('pending sample');
   try{
    const t=now();if(failed||t.wall>=stopWall||history.length===4)return {decision:'cleanup'};
    const i=history.length,gap=offsets[i]-(i?offsets[i-1]:0),due=Math.max(offsets[i],(history.at(-1)??0)+gap);
    if(start.wall+due>=stopWall)return {decision:'cleanup'};
    if(t.elapsed<due)return {decision:'independent_work',notBeforeWall:start.wall+due};
    pending=true;
    // No tool/model boundary between local eligibility and this UI call.
    const ax=await app.getAXState({disableDiffing:true});const end=now();
    if(end.wall>=stopWall)throw Error('late observation');
    let outcome,value;
    try{value=assess(ax);outcome='ready'}catch(e){if(e.message!=='busy')throw e;outcome='busy'}
    history.push(end.elapsed);return {decision:'observed',ordinal:history.length,outcome,assessment:value,ax};
   }catch(e){failed=true;throw e}finally{pending=false}
  },
  snapshot(){return {session,start:{...start},stopWall,cleanupWall,history:[...history],failed,pending}}
 });
}
