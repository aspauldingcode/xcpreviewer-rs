// Offline proposal: terminal session policy around reviewed sampling/action adapters.
import {guardedClick} from './action.mjs';
export function createDriver({gate,app,binding,stopMs,clock=Date.now}){
 const b={projects:[...binding.projects],sources:[...binding.sources]};let terminal=false,reason=null,pending=false;const attempts={refresh:0,selection:0},dispatch={refresh:0,selection:0};let kind=null;
 const fail=e=>{terminal=true;reason??=e.message??String(e);return e};
 const wrapped={async getAXState(options){const ax=await app.getAXState(options);if(terminal)throw Error('session terminal');return ax},async click(index){if(terminal)throw Error('session terminal');dispatch[kind]++;return app.click(index)}};
 async function perform(work){if(terminal)throw Error('session terminal');if(pending)throw fail(Error('concurrent operation'));pending=true;try{return await work()}catch(e){throw fail(e)}finally{pending=false;kind=null}}
 return Object.freeze({
  sample(assess){return perform(async()=>{const result=await gate.sample(wrapped,assess);if(result.decision==='cleanup'){terminal=true;reason='sampler cleanup'}return result})},
  action(previous,requested){return perform(async()=>{if(!Object.hasOwn(attempts,requested)||attempts[requested]!==0)throw Error('action attempt bound');kind=requested;attempts[requested]++;return guardedClick(wrapped,previous,b,requested,stopMs,clock)})},
  abort(message){fail(Error(message));},
  snapshot(){return {terminal,reason,pending,attempts:{...attempts},dispatch_attempts:{...dispatch},scope:'Dispatch attempt is not verified effect; clocks/config/app are trusted model inputs'}}
 });
}
