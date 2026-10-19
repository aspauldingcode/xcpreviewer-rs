// Research-only callback coordinator. No UI provider binding or native authority.
export function createSettlement({binding,deadline,clock,closeOwned,zeroOwned}) {
 const owner=Object.freeze({...binding});
 if(typeof owner.project!=='string'||!owner.project||typeof owner.nonce!=='string'||!owner.nonce||!Number.isFinite(deadline)||typeof clock!=='function')throw Error('configuration');
 let terminal=false,reason=null,serial=0,cleanupPending=false,cleanupAttempted=false,closure=null;
 let lastClock=-Infinity,expired=false,clockInvalid=false;
 const pending=new Map(),attempts={open:0,observe:0},journal=[];
 const now=()=>{if(clockInvalid)throw Error('clock invalid');let n;try{n=clock()}catch{n=NaN}if(!Number.isFinite(n)||n<lastClock){clockInvalid=true;terminal=true;reason??='clock invalid';throw Error('clock invalid')}lastClock=n;if(n>=deadline)expired=true;return n};
 const matches=b=>b?.project===owner.project&&b?.nonce===owner.nonce;
 function snapshot(){return {terminal,reason,expired,clock_invalid:clockInvalid,pending_operations:[...pending.values()].map(v=>({...v})),cleanup_pending:cleanupPending,cleanup_attempted:cleanupAttempted,closure:closure?{...closure}:null,attempts:{...attempts},journal:[...journal],native_eligible:false,scope:'Trusted injected callbacks and complete registration only; no unseen effects or backend cancellation proof'};}
 function stop(why='stop'){terminal=true;reason??=why;journal.push('stop');}
 function begin(kind,dispatch) {
  if(terminal)throw Error('terminal');
  if(now()>=deadline){stop('deadline');throw Error('deadline');}
  if(!Object.hasOwn(attempts,kind)||attempts[kind]!==0||pending.size!==0)throw Error('operation bound');
  attempts[kind]++;const id=++serial;pending.set(id,{id,kind});journal.push(kind+':begin');
  return Promise.resolve().then(()=>{if(terminal||now()>=deadline)throw Error('terminal before dispatch');journal.push(kind+':dispatch');return dispatch(owner)}).then(value=>{journal.push(kind+':resolved');return value},error=>{stop('operation rejected');journal.push(kind+':rejected');throw error}).finally(()=>{pending.delete(id);journal.push(kind+':settled');});
 }
 async function reconcile() {
  stop('cleanup');
  try{now()}catch{} // Clock failure never prevents owned cleanup, but denies timeliness.
  // Timeout of a wrapper is not settlement of the operation it raced.
  if(pending.size!==0)return {clean:false,pending:true,cleanup_deadline_met:false,native_eligible:false};
  if(cleanupPending)throw Error('cleanup pending');
  if(cleanupAttempted)return {...closure};
  cleanupAttempted=true;cleanupPending=true;journal.push('close:begin');
  try {
   const closed=await closeOwned(owner);
   if(!true||closed?.closed!==true)throw Error('owned close receipt');
   journal.push('close:settled');
   const zero=await zeroOwned(owner);
   if(!matches(zero?.binding)||!Number.isInteger(zero?.count)||zero.count!==0)throw Error('fresh zero receipt');
   journal.push('zero:observed');
   let t=null;try{t=now()}catch{}
   closure={clean:true,pending:false,cleanup_deadline_met:!clockInvalid&&!expired&&t<deadline,cleanup_observed_at:t,clock_invalid:clockInvalid,native_eligible:false};
  } catch(error) {
   closure={clean:false,pending:false,cleanup_deadline_met:false,error:error.message??String(error),native_eligible:false};journal.push('cleanup:failed');
  } finally {cleanupPending=false;}
  return {...closure};
 }
 now();
 return Object.freeze({begin,stop,reconcile,snapshot});
}
// Keeping finally in one invocation removes model-turn boundaries only. A hung
// callback still prevents completion: bounded/cancellable provider settlement is
// an independent missing prerequisite, never inferred from this helper.
export async function runSingleCall(config,open,observe) {
 const session=createSettlement(config);let failure=null;
 try {await session.begin('open',open);await session.begin('observe',observe);}
 catch(error){failure=error.message??String(error);}
 finally {await session.reconcile();}
 return {failure,...session.snapshot()};
}
