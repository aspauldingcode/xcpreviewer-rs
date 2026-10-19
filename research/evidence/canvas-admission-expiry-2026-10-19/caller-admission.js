if(Object.hasOwn(globalThis,'xcpreviewerNativeAdmission'))throw Error('admission already installed');
globalThis.xcpreviewerNativeAdmission=(()=>{
// Pure trusted-record gate; no UI I/O or filesystem authentication.
function assess(ax,b){
 const need=(v,m)=>{if(!v)throw Error(m)};need(typeof ax==='string'&&ax.length<=262144,'AX shape');
 const nodes=[],stack=[],seen=new Set();
 for(const line of ax.split('\n')){const m=line.match(/^(\t*)(\d+) (.*)$/);if(!m)continue;const depth=m[1].length,index=Number(m[2]);need(!seen.has(index),'duplicate index');seen.add(index);while(stack.length&&stack.at(-1).depth>=depth)stack.pop();need(depth===stack.length,'depth');const n={depth,index,label:m[3],parent:stack.at(-1)?.index??null,ancestors:stack.map(x=>x.index)};nodes.push(n);stack.push(n);}
 const attr=(s,k)=>{const hits=[...s.matchAll(new RegExp('(?:^|, )'+k+': ([^,\\n]+)(?=, |$)','g'))];need(hits.length===1,'attribute '+k);return hits[0][1]};
 need(b&&Array.isArray(b.projects)&&Array.isArray(b.sources)&&b.projects.length===2&&b.sources.length===2&&[...b.projects,...b.sources].every(x=>typeof x==='string'),'binding');
 const roots=nodes.filter(n=>n.depth===0&&n.label.startsWith('standard window '));need(roots.length===1&&roots[0].index===0,'root');const root=roots[0];need(attr(root.label,'ID')==='Xcode.WorkspaceWindow','window ID');const url=new URL(attr(root.label,'URL'));need(url.protocol==='file:'&&!url.host&&!url.search&&!url.hash,'local URL');need(b.sources.includes(decodeURIComponent(url.pathname)),'source context');
 const tabs=nodes.filter(n=>n.parent===root.index&&n.label.startsWith('split group PreviewLab.xcodeproj, '));need(tabs.length===1&&tabs[0].index===1&&attr(tabs[0].label,'ID')==='Workspace window tab content'&&b.projects.includes(attr(tabs[0].label,'Description')),'project');
 const inside=n=>n.ancestors.includes(1)&&!n.ancestors.some(i=>nodes.find(x=>x.index===i)?.label.includes('Description: Source Editor'));
 const activity=nodes.filter(n=>n.label.includes('ID: Activity Text'));need(activity.length===1&&/: Ready(?: │|,)/.test(activity[0].label)&&!nodes.some(n=>n.label.startsWith('busy indicator ')),'busy');
 const refresh=nodes.filter(n=>n.label==='button Description: Refresh Canvas, ID: arrow.clockwise'&&inside(n)),paused=nodes.filter(n=>n.label==='text Canvas paused'&&inside(n));
 const titles=['text Primary layers','text Text and interaction','text Layout edit'].map(s=>nodes.filter(n=>n.label===s&&inside(n)));const live=nodes.filter(n=>n.label==='menu button (selected) Description: Live, ID: play.circle.fill'&&inside(n)),pins=nodes.filter(n=>n.label==='button Description: Pin Preview, ID: pin'&&inside(n));let selection=null;
 if(titles.every(a=>a.length===1)&&live.length===1&&pins.length===1){const t=titles.map(a=>a[0]),list=nodes.find(n=>n.index===t[0].parent),pane=nodes.find(n=>n.index===list?.parent);if(list?.label==='scroll area'&&pane?.label==='container'&&t.every(n=>n.parent===list.index)&&pins[0].parent===list.index&&live[0].parent===pane.index)selection=t[1].index;}
 const signature=JSON.stringify(nodes.map(n=>[n.depth,n.index,n.label,n.parent]));
 return {signature,refresh:refresh.length===1&&paused.length===1&&refresh[0].parent===paused[0].parent?refresh[0].index:null,selection};
}
function authorize(previous,fresh,kind,now,stop){if(!previous||previous.signature!==fresh.signature)throw Error('stale');if(!Number.isFinite(now)||!Number.isFinite(stop)||now>=stop)throw Error('deadline');if(!['refresh','selection'].includes(kind)||fresh[kind]===null)throw Error('unqualified');return fresh[kind];}
function normalize(ax){
 const marker='\nSelected:\n';if(!ax.includes(marker))return ax;
 if(ax.split(marker).length!==2)throw Error('Multiple Selected summaries');
 const [tree,tail]=ax.split(marker),sep='\n\nNote: Pay special attention to the content selected by the user. If the user asks a question or refers to the content they are looking at on-screen, they might be referring to the selected content (but they might be referring to something else that\'s visible, too).';
 if(!tail.includes(sep))throw Error('Unknown Selected footer');
 const remainder=tail.slice(tail.indexOf(sep)+sep.length);if(!['','\n'].includes(remainder))throw Error('Unknown footer content');
 const summary=tail.slice(0,tail.indexOf(sep)),known=new Map();
 for(const line of tree.split('\n')){const m=line.match(/^\t*(\d+) (.*)$/);if(!m)continue;const i=Number(m[1]);if(known.has(i))throw Error('Duplicate tree index');known.set(i,m[2]);}
 const rows=summary.split('\n'),seen=new Set();if(rows.length<1||rows.length>16)throw Error('Selected summary bound');
 for(const row of rows){const m=row.match(/^\t(\d+) (.*)$/);if(!m)throw Error('Selected row syntax');const i=Number(m[1]);if(seen.has(i)||known.get(i)!==m[2]||!m[2].includes('(selected)'))throw Error('Selected row mismatch');seen.add(i);}
 return tree;
}
function assessReport(ax,b){return assess(normalize(ax),b);}
{authorize};
// Offline proposal. UI metadata is not source/lease authentication.
const footer="\n\nNote: Pay special attention to the content selected by the user. If the user asks a question or refers to the content they are looking at on-screen, they might be referring to the selected content (but they might be referring to something else that's visible, too).";
function qualifyWelcome(ax,binding){
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
function qualifyOpened(ax,binding){
 // Pinned assessReport validates source/project context before checking busy.
 try{assessReport(ax,binding)}catch(e){if(e.message!=='busy')throw e;}
 return true;
}
function createOwnedOpener({app,binding,stopMs,clock=Date.now}){
 const b={projects:[...binding.projects],sources:[...binding.sources]};let attempted=false,pending=false,terminal=false,reason=null,dispatchAttempts=0,openedObserved=false;
 const check=()=>{if(terminal)throw Error('opening terminal');const t=clock();if(!Number.isFinite(t)||!Number.isFinite(stopMs)||t>=stopMs)throw Error('opening deadline')};
 return Object.freeze({async open(){
  if(attempted||terminal){terminal=true;reason??='opening attempt consumed';throw Error('opening attempt consumed');}attempted=true;pending=true;
  try{check();const before=await app.getAXState({disableDiffing:true});const index=qualifyWelcome(before,b);check();dispatchAttempts++;await app.click(index,{clickCount:2});const after=await app.getAXState({disableDiffing:true});check();qualifyOpened(after,b);openedObserved=true;terminal=true;reason='owned workspace observed';return {openedObserved:true,source_authenticated:false};}
  catch(e){terminal=true;reason=e.message??String(e);throw e}finally{pending=false}
 },snapshot(){return {attempted,pending,terminal,reason,dispatchAttempts,openedObserved,scope:'Opening dispatch is not proof of transient process behavior; source/lease identity external'}}});
}
// Research proposal: closure/lease records are trusted inputs, not authenticated here.
function admitFresh({registry,previous,closure,config,clock,app,binding}){
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
return Object.freeze({admitFresh,createOwnedOpener});})();
