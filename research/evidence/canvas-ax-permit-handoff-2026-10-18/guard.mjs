// Pure trusted-record gate; no UI I/O or filesystem authentication.
export function assess(ax,b){
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
export function authorize(previous,fresh,kind,now,stop){if(!previous||previous.signature!==fresh.signature)throw Error('stale');if(!Number.isFinite(now)||!Number.isFinite(stop)||now>=stop)throw Error('deadline');if(!['refresh','selection'].includes(kind)||fresh[kind]===null)throw Error('unqualified');return fresh[kind];}
