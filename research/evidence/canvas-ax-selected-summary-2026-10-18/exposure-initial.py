"""Inspect one owned CUA AX projection; this grants no native-action authority."""
import re
from path_binding import assess
IDS=('owned.callback.root','owned.callback.count','owned.callback.increment')
def scan(ax,binding):
 ownership=assess(ax,binding);nodes=[];stack=[]
 for line in ax.splitlines():
  m=re.fullmatch(r'(\t*)(\d+) (.*)',line)
  if not m:continue
  depth=len(m[1]);index=int(m[2]);label=m[3]
  while stack and stack[-1]['depth']>=depth:stack.pop()
  node={'depth':depth,'index':index,'label':label,'ancestors':[n['index'] for n in stack]};nodes.append(node);stack.append(node)
 editor={n['index'] for n in nodes if 'Description: Source Editor' in n['label']}
 matches={name:[] for name in IDS}
 for n in nodes:
  if 1 not in n['ancestors'] or n['index'] in editor or any(i in editor for i in n['ancestors']):continue
  ids=re.findall(r'(?:^|, )ID: ([^,\n]+)(?=, |$)',n['label'])
  if len(ids)==1 and ids[0] in matches:matches[ids[0]].append(n)
 return {'ownership':ownership,'matches':matches,'unique_all_identifiers_observed':all(len(v)==1 for v in matches.values()),'scope':'One current CUA owned-window AX representation outside SourceEditor only; not global OS accessibility absence or action qualification.','native_action_authorized':False}
