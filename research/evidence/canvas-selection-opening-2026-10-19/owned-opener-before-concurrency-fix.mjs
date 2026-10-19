// Offline proposal. UI metadata is not source/lease authentication.
import {assessReport} from './normalized-guard.mjs';
const footer="\n\nNote: Pay special attention to the content selected by the user. If the user asks a question or refers to the content they are looking at on-screen, they might be referring to the selected content (but they might be referring to something else that's visible, too).";
export function qualifyWelcome(ax,binding){
 if(typeof ax!=='string'||ax.length>262144)throw Error('Welcome AX shape');
 const parts=ax.split('\nSelected:\n');if(parts.length>2)throw Error('Welcome summary count');
 const tree=parts[0],lines=tree.split('\n'),nodes=[],stack=[],seen=new Set();
 for(let i=0;i<lines.length;i++){
  const m=lines[i].match(/^(\t*)(\d+) (.*)$/);if(!m)continue;
  const depth=m[1].length,index=Number(m[2]);if(!Number.isSafeInteger(index)||seen.has(index))throw Error('Welcome duplicate/index');seen.add(index);
  while(stack.length&&stack.at(-1).depth>=depth)stack.pop();if(stack.length!==depth)throw Error('Welcome depth');
  const n={depth,index,label:m[3],parent:stack.at(-1),line:i};nodes.push(n);stack.push(n);
 }
 const roots=nodes.filter(n=>n.depth===0&&n.label.startsWith('window '));
 if(roots.length!==1||roots[0].index!==0||roots[0].label!=='window Welcome to Xcode, ID: Welcome, Secondary Actions: Raise')throw Error('Welcome window');
 if(parts.length===2){
  const cut=parts[1].indexOf(footer);if(cut<0||!['','\n'].includes(parts[1].slice(cut+footer.length)))throw Error('Welcome footer');
  const m=parts[1].slice(0,cut).match(/^\t(\d+) row \(selected\)$/);if(!m||!nodes.some(n=>n.index===Number(m[1])&&n.label.startsWith('row (selected) ')))throw Error('Welcome summary');
 }
 if(!binding||!Array.isArray(binding.projects)||binding.projects.length!==2||binding.projects.some(x=>typeof x!=='string'||!x.endsWith('/PreviewLab.xcodeproj')))throw Error('Welcome binding');
 const folders=binding.projects.map(x=>x.slice(0,-'/PreviewLab.xcodeproj'.length));
 const candidates=nodes.filter(n=>/^row \(select(?:ed|able)\) PreviewLab$/.test(n.label)&&folders.includes(lines[n.line+1])&&n.depth===4&&n.parent?.label==='list Recent Projects'&&n.parent.parent?.label==='scroll area'&&n.parent.parent.parent?.label==='container'&&n.parent.parent.parent.parent===roots[0]);
 if(candidates.length!==1)throw Error('Welcome owned row');return candidates[0].index;
}
export function qualifyOpened(ax,binding){
 // Pinned assessReport validates source/project context before checking busy.
 try{assessReport(ax,binding)}catch(e){if(e.message!=='busy')throw e;}
 return true;
}
export function createOwnedOpener({app,binding,stopMs,clock=Date.now}){
 const b={projects:[...binding.projects],sources:[...binding.sources]};let attempted=false,pending=false,terminal=false,reason=null,dispatchAttempts=0,openedObserved=false;
 const check=()=>{const t=clock();if(!Number.isFinite(t)||!Number.isFinite(stopMs)||t>=stopMs)throw Error('opening deadline')};
 return Object.freeze({async open(){
  if(attempted||terminal)throw Error('opening attempt consumed');attempted=true;pending=true;
  try{check();const before=await app.getAXState({disableDiffing:true});const index=qualifyWelcome(before,b);check();dispatchAttempts++;await app.click(index,{clickCount:2});const after=await app.getAXState({disableDiffing:true});check();qualifyOpened(after,b);openedObserved=true;terminal=true;reason='owned workspace observed';return {openedObserved:true,source_authenticated:false};}
  catch(e){terminal=true;reason=e.message??String(e);throw e}finally{pending=false}
 },snapshot(){return {attempted,pending,terminal,reason,dispatchAttempts,openedObserved,scope:'Opening dispatch is not proof of transient process behavior; source/lease identity external'}}});
}
