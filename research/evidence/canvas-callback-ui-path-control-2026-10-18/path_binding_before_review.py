"""Trusted recorded path equivalence and AX ownership checks, not an OS security boundary."""
import re,urllib.parse

def need(v,m):
 if not v:raise ValueError(m)
def validate_binding(b):
 need(type(b) is dict and set(b)=={'project','source'},'binding keys')
 for kind,entry in b.items():
  need(set(entry)=={'requested','observed','canonical','requested_stat','observed_stat'},'binding fields')
  a,c=entry['requested'],entry['observed']
  need(type(a) is str and a.startswith('/private/tmp/callback-ui-access-20261018/workspace/'),'requested scope')
  need(c=='/tmp/'+a[len('/private/tmp/'):],'measured alias only')
  need(entry['canonical']==a,'canonical identity')
  for st in [entry['requested_stat'],entry['observed_stat']]:
   need(type(st) is list and len(st)==2 and all(type(x) is int and x>=0 for x in st),'stat identity types')
  need(entry['requested_stat']==entry['observed_stat'],'inode identity')
 need(b['project']['requested'].endswith('/PreviewLab.xcodeproj'),'project suffix')
 need(b['source']['requested']==b['project']['requested'].replace('/PreviewLab.xcodeproj','/Sources/PreviewLab/PreviewLab.swift'),'source relation')
 return b
def attribute(label,key):
 values=re.findall(r'(?:^|, )'+re.escape(key)+r': ([^,\n]+)(?=, |$)',label)
 need(len(values)==1,'unique '+key)
 return values[0]
def assess(ax,b,source_required=True):
 validate_binding(b);need(type(ax) is str and len(ax)<=262144,'AX shape')
 nodes=[];seen=set()
 for line in ax.splitlines():
  m=re.fullmatch(r'(\t*)(\d+) (.*)',line)
  if not m:continue
  index=int(m[2]);need(index not in seen,'duplicate indices');seen.add(index);nodes.append((len(m[1]),index,m[3]))
 roots=[n for n in nodes if n[0]==0 and n[2].startswith('standard window ')]
 need(len(roots)==1 and roots[0][1]==0,'one root')
 need(attribute(roots[0][2],'ID')=='Xcode.WorkspaceWindow','workspace ID')
 raw=attribute(roots[0][2],'URL');url=urllib.parse.urlsplit(raw)
 need(url.scheme=='file' and not url.netloc and not url.query and not url.fragment,'local URL')
 path=urllib.parse.unquote(url.path)
 allowed={b['source']['requested'],b['source']['observed']}
 if not source_required:allowed|={b['project']['requested'],b['project']['observed']}
 need(path in allowed,'exact source context')
 tabs=[n for n in nodes if n[0]==1 and n[2].startswith('split group PreviewLab.xcodeproj, ')]
 need(len(tabs)==1 and tabs[0][1]==1,'unique project tab')
 need(attribute(tabs[0][2],'ID')=='Workspace window tab content','tab ID')
 need(attribute(tabs[0][2],'Description') in {b['project']['requested'],b['project']['observed']},'project identity')
 closes=[n[1] for n in nodes if n[0]==1 and n[2]=='close button'];need(len(closes)==1,'unique close')
 return {'close_index':closes[0],'source_context':path in {b['source']['requested'],b['source']['observed']}}
