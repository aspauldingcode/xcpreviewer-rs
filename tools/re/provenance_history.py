"""Bounded path-addition ancestry audit; Git ordering never proves clean authorship."""
import argparse,json,subprocess,time
from pathlib import Path
from canvas_graph import ROOT,safe

PATHS=['tools/re/rust/canvas-core/src/contract.rs','tools/re/rust/canvas-core/src/wasm-template.rs','tools/re/rust/canvas-core/src/lib.rs','tools/re/reloop/live_wasm_host.js','tools/re/reloop/source_revision_host.js','tools/re/preview_mcp_stdio.js']
ANCHORS=['docs/reverse-engineering/2026-10-08-initial-findings.md','docs/reverse-engineering/2026-10-09-unfulfilled-deinit.md']


def audit(root,paths=None,anchors=None):
 root=Path(root).resolve();paths=PATHS if paths is None else paths;anchors=ANCHORS if anchors is None else anchors
 if not paths or len(paths)>32 or not anchors or len(anchors)>8:raise ValueError('History scope limit')
 for name in paths+anchors:safe(root,name)
 deadline=time.monotonic()+60
 def git(*args,allow_absent=False):
  remaining=deadline-time.monotonic()
  if remaining<=0:raise ValueError('History audit deadline')
  r=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=min(15,remaining))
  if len(r.stdout.encode())>1048576:raise ValueError('History output limit')
  if r.returncode not in ([0,1] if allow_absent else [0]):r.check_returncode()
  return r
 def additions(name):
  rows=git('log','--diff-filter=A','--format=%H','--',name).stdout.splitlines()
  if len(rows)>32:raise ValueError('Too many path additions')
  out=[]
  for commit in rows:
   # Capture object identities, not proprietary or reconstruction source text.
   tree=git('ls-tree',commit,'--',name).stdout.strip()
   if not tree:raise ValueError('Addition object missing')
   out.append({'commit':commit,'tree_entry':tree})
  return out
 def ancestor(a,b):return git('merge-base','--is-ancestor',a,b,allow_absent=True).returncode==0
 reference=[{'path':p,'additions':additions(p)} for p in anchors]
 rows=[]
 for name in paths:
  added=additions(name);comparisons=[]
  for ref in reference:
   for a in ref['additions']:
    for b in added:comparisons.append({'analysis_path':ref['path'],'analysis_addition':a['commit'],'candidate_addition':b['commit'],'analysis_is_ancestor':ancestor(a['commit'],b['commit']),'same_commit':a['commit']==b['commit']})
  rows.append({'path':name,'additions':added,'comparisons':comparisons,'origin':'not-established','clean_handoff_eligible':False,'disposition':'quarantined-pending-independent-provenance-review'})
 return {'schema_version':1,'head':git('rev-parse','HEAD').stdout.strip(),'history_method':'Path additions only, no rename-following, no claim of initial conceptual authorship','analysis_anchors':reference,'candidates':rows,'limits':{'paths':32,'anchors':8,'additions_per_path':32,'total_seconds':60,'subprocess_seconds':15},'conclusion':'Ancestry establishes repository ordering only. It does not establish file derivation, agent exposure, originality, license or independent implementation.','independent_review_complete':False,'task_accepted':False}


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);args=p.parse_args();print(json.dumps(audit(args.root),indent=2))
