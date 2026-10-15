import hashlib,json,re
from pathlib import Path

def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text())
 assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for name,row in m['files'].items():
  p=e/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
 d=json.loads((e/'history.json').read_text());assert d['head']=='1da896c787784ee462f5da1b08f60b74c84fc010'
 expected=['tools/re/rust/canvas-core/src/contract.rs','tools/re/rust/canvas-core/src/wasm-template.rs','tools/re/rust/canvas-core/src/lib.rs','tools/re/reloop/live_wasm_host.js','tools/re/reloop/source_revision_host.js','tools/re/preview_mcp_stdio.js']
 assert [r['path'] for r in d['candidates']]==expected
 anchors=d['analysis_anchors'];assert [a['path'] for a in anchors]==['docs/reverse-engineering/2026-10-08-initial-findings.md','docs/reverse-engineering/2026-10-09-unfulfilled-deinit.md']
 assert [a['additions'][0]['commit'] for a in anchors]==['22bfe6b32e781e8532196c2ff573d19840081e23','33688a773420254080fcf5d22121a073f1edbcaa']
 baseline=json.loads((e/'independent-ancestry.json').read_text());assert len(baseline)==12
 for i,row in enumerate(d['candidates']):
  assert row['origin']=='not-established' and row['clean_handoff_eligible'] is False and row['disposition']=='quarantined-pending-independent-provenance-review'
  assert len(row['additions'])==1 and len(row['comparisons'])==2
  addition=row['additions'][0];assert re.fullmatch('[0-9a-f]{40}',addition['commit'])
  assert re.fullmatch('100644 blob [0-9a-f]{40}\\t'+re.escape(row['path']),addition['tree_entry'])
  for j,pair in enumerate(row['comparisons']):
   anchor=anchors[j]['additions'][0]['commit'];assert pair=={'analysis_path':anchors[j]['path'],'analysis_addition':anchor,'candidate_addition':addition['commit'],'analysis_is_ancestor':True,'same_commit':False}
   check=baseline[i*2+j];assert check['path']==row['path'] and check['analysis_addition']==anchor and check['candidate_addition']==addition['commit']
   assert check['command']==['git','rev-list','--ancestry-path',anchor+'..'+addition['commit']] and check['code']==0 and check['stderr']==''
   assert addition['commit'] in check['commits'] and anchor not in check['commits'] and len(check['commits'])==len(set(check['commits'])) and all(re.fullmatch('[0-9a-f]{40}',x) for x in check['commits'])
 assert d['task_accepted'] is d['independent_review_complete'] is False
 a=json.loads((e/'assessment.json').read_text());assert a=={'prior_inventory_seal_verified':True,'repository_order_only':True,'native_acquisition':False,'product_edits':False,'independent_review_complete':False,'handoff_eligible':0}
 return {'candidate_paths':6,'analysis_anchors':2,'ancestry_checks':12,'handoff_eligible':0,'independent_review_complete':False,'task_accepted':False}
