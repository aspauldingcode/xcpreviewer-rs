// Trusted CUA observation guard for this exact pinned, owned fixture. No UI I/O.
export const PROJECT='/private/tmp/callback-ui-access-20261018/workspace/PreviewLab.xcodeproj';
export const SOURCE=PROJECT.replace('/PreviewLab.xcodeproj','/Sources/PreviewLab/PreviewLab.swift');
export function assess(ax){
 if(typeof ax!=='string'||ax.length>262144)throw Error('AX shape');
 const nodes=[],stack=[],seen=new Set();
 for(const line of ax.split('\n')){
  const m=line.match(/^(\t*)(\d+) (.*)$/);if(!m)continue;
  const depth=m[1].length,index=Number(m[2]),label=m[3];
  if(seen.has(index))throw Error('duplicate index');seen.add(index);
  while(stack.length&&stack.at(-1).depth>=depth)stack.pop();
  const node={depth,index,label,parents:[...stack]};nodes.push(node);stack.push(node);
 }
 const roots=nodes.filter(n=>n.depth===0&&n.label.startsWith('standard window '));
 if(roots.length!==1||roots[0].index!==0||!roots[0].label.includes('ID: Xcode.WorkspaceWindow,'))throw Error('window');
 const raw=roots[0].label.match(/, URL: (\S+)$/)?.[1];if(!raw)throw Error('URL');const url=new URL(raw);
 if(url.protocol!=='file:'||url.host||url.search||url.hash||decodeURIComponent(url.pathname)!==SOURCE)throw Error('source');
 const project=nodes.filter(n=>n.index===1&&n.depth===1&&n.label===`split group PreviewLab.xcodeproj, ID: Workspace window tab content, Description: ${PROJECT}`);
 if(project.length!==1)throw Error('project');
 const activity=nodes.filter(n=>n.label.includes('ID: Activity Text'));
 if(activity.length!==1||!/: Ready(?: │|,)/.test(activity[0].label)||nodes.some(n=>n.label.startsWith('busy indicator ')))throw Error('busy');
 const outsideEditor=n=>n.parents.some(p=>p.index===1&&p.label===project[0].label)&&!n.parents.some(p=>p.label.includes('Description: Source Editor'));
 const refresh=nodes.filter(n=>n.label==='button Description: Refresh Canvas, ID: arrow.clockwise'&&outsideEditor(n));
 const paused=nodes.filter(n=>n.label==='text Canvas paused'&&outsideEditor(n));
 let refreshIndex=null;
 if(refresh.length===1&&paused.length===1&&refresh[0].parents.at(-1)?.index===paused[0].parents.at(-1)?.index)refreshIndex=refresh[0].index;
 const preview=n=>n.parents.some(p=>p.label==='container Description: Canvas')&&n.parents.some(p=>p.label==='container Description: Text and interaction')&&outsideEditor(n);
 const counts=nodes.filter(n=>/^text Count: \d+$/.test(n.label)&&preview(n));
 const buttons=nodes.filter(n=>n.label==='button Increment'&&preview(n));
 const previewParent=n=>n.parents.findLast(p=>p.label==='container Description: Text and interaction')?.index;
 const increment=counts.length===1&&buttons.length===1&&previewParent(counts[0])===previewParent(buttons[0])?buttons[0].index:null;
 const relevant=nodes.filter(n=>refresh.includes(n)||paused.includes(n)||counts.includes(n)||buttons.includes(n));
 const titleLabels=['text Primary layers','text Text and interaction','text Layout edit'];
 const titleNodes=titleLabels.map(label=>nodes.filter(n=>n.label===label&&outsideEditor(n)));
 let selection=null;
 if(titleNodes.every(a=>a.length===1)){
  const titles=titleNodes.map(a=>a[0]),list=titles[0].parents.at(-1),pane=list?.parents.at(-1);
  const lives=nodes.filter(n=>n.label==='menu button (selected) Description: Live, ID: play.circle.fill'&&outsideEditor(n));
  const pins=nodes.filter(n=>n.label==='button Description: Pin Preview, ID: pin'&&outsideEditor(n));
  if(list?.label==='scroll area'&&pane?.label==='container'&&titles.every(n=>n.parents.at(-1)?.index===list.index)&&lives.length===1&&lives[0].parents.at(-1)?.index===pane.index&&pins.length===1&&pins[0].parents.at(-1)?.index===list.index){
   selection={index:titles[1].index,signature:JSON.stringify([...titles,lives[0],pins[0]].map(n=>[n.index,n.label,n.parents.map(p=>[p.index,p.label])]))};
  }
 }
 return {signature:JSON.stringify(relevant.map(n=>[n.index,n.label,n.parents.map(p=>[p.index,p.label])])),refresh:refreshIndex,increment,count:counts.length===1?Number(counts[0].label.slice(12)):null,selection};
}
export function authorize(previous,fresh,kind,now,stop){
 if(!previous||previous.signature!==fresh.signature)throw Error('stale signature');
 if(!Number.isFinite(now)||!Number.isFinite(stop)||now>=stop)throw Error('deadline');
 if(kind==='refresh'&&fresh.refresh!==null)return fresh.refresh;
 if(kind==='increment'&&fresh.increment!==null&&fresh.count===0)return fresh.increment;
 throw Error('unqualified control');
}

export function authorizeSelection(previous,fresh,now,stop){
 if(!previous?.selection||!fresh?.selection||previous.selection.signature!==fresh.selection.signature)throw Error('unqualified or stale title list');
 if(!Number.isFinite(now)||!Number.isFinite(stop)||now>=stop)throw Error('selection deadline');
 return fresh.selection.index;
}
