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
// Offline proposal: instantiate once per fixed owned session, inside the UI caller.
// The outer controller lease still owns exclusive backend access and cleanup.
function createReadiness(config,clock){
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
function createSessionRegistry(){
 const sessions=new Map();
 return Object.freeze({bind(config,clock){
  const {session,workspace,source_sha256,stopWall,cleanupWall}=config;
  if(typeof session!=='string'||!/^[0-9a-f]{32}$/.test(session)||typeof workspace!=='string'||!workspace.startsWith('/private/tmp/')||!workspace.endsWith('/PreviewLab.xcodeproj')||typeof source_sha256!=='string'||!/^[0-9a-f]{64}$/.test(source_sha256))throw Error('owned session configuration');
  if(sessions.has(session))throw Error('session already bound');
  const context=Object.freeze({session,workspace,source_sha256,stopWall,cleanupWall}),gate=createReadiness(context,clock);
  const bound=Object.freeze({sample:(app,assess)=>gate.sample(app,assess),snapshot:()=>({...gate.snapshot(),context:{...context}})});sessions.set(session,bound);return bound;
 }});
}
async function guardedClick(app,previous,binding,kind,stop,clock=Date.now){
 const ax=await app.getAXState({disableDiffing:true});
 if(typeof ax!=='string'||ax.length>262144)throw Error('AX shape');
 const fresh=assessReport(ax,binding);
 const index=authorize(previous,fresh,kind,clock(),stop);
 await app.click(index);
 return app.getAXState({disableDiffing:true});
}
// Research proposal: execute only during separately reviewed fresh-session initialization.
// Never recreate missing state to resume an active or failed native experiment.
if(!Object.hasOwn(globalThis,'xcpreviewerOwnedRegistry'))globalThis.xcpreviewerOwnedRegistry=createSessionRegistry();
if(!globalThis.xcpreviewerOwnedRegistry||typeof globalThis.xcpreviewerOwnedRegistry.bind!=='function'||!Object.isFrozen(globalThis.xcpreviewerOwnedRegistry))throw Error('registry context invalid');
