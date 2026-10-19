// Research-only adapter. No native execution authority or cleanup implementation.
// The caller supplies a reviewed driver, binding assessor and immutable lease.
export function createSelectionOnly({driver,assess}) {
 let pending=false,terminal=false,reason=null,attempted=false;
 const fail=e=>{terminal=true;reason??=e.message??String(e);driver.abort(reason);return e};
 return Object.freeze({
  async next(){
   if(terminal)throw Error('selection session terminal');
   if(pending)throw fail(Error('concurrent selection operation'));
   pending=true;
   try {
    const result=await driver.sample(assess);
    if(terminal)throw Error('selection session terminal');
    if(result.decision==='cleanup'){terminal=true;reason='sampler cleanup';return {decision:'cleanup'};}
    if(result.decision!=='observed')return {decision:result.decision,notBeforeWall:result.notBeforeWall};
    if(result.outcome==='busy'||result.assessment?.selection===null)return {decision:'wait',ordinal:result.ordinal,outcome:result.outcome};
    if(result.outcome!=='ready'||!Number.isInteger(result.assessment?.selection))throw Error('selection assessment shape');
    // No caller/model boundary between passive qualification and fresh action guard.
    attempted=true;
    await driver.action(result.assessment,'selection');
    terminal=true;reason='selection dispatched; outcome requires independent observation';
    return {decision:'selection_dispatched',effect_verified:false};
   }catch(e){throw fail(e)}finally{pending=false}
  },
  snapshot(){return {pending,terminal,reason,selection_attempted:attempted,driver:driver.snapshot()};}
 });
}
