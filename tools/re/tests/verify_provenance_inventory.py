import hashlib,json
from pathlib import Path

def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text())
 assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for name,row in m['files'].items():
  p=e/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink()
  raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 first=json.loads((e/'inventory.json').read_text());report=json.loads((e/'inventory-v2.json').read_text())
 assert first['counts']['files']==155 and report['counts']=={'files':159,'assets':0,'inventory_errors':0,'handoff_eligible':0}
 assert set(report['declared_roots'])-set(first['declared_roots'])=={'tools/re/preview_stdio.js','tools/re/preview_mcp_stdio.js','tools/re/preview_cli.py','tools/re/rust_source_cli.py'}
 assert report['head']==first['head']=='5db63af17b4cf036065e87a984bacf4a2b0a7f3c'
 rows=report['files'];assert len(rows)==len({r['path'] for r in rows})==159
 previous={r['path']:r for r in first['files']}
 assert all(previous[row['path']]==row for row in rows if row['path'] in previous)
 for row in rows:
  assert row['classification']=='quarantined-pending-provenance-review' and row['clean_handoff_eligible'] is False and row['origin']=='not-established' and row['license']=='not-assessed'
  assert row['tracking'] in ['tracked','untracked'] and row['kind']=='source-or-project-metadata'
  assert not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts
  assert len(row['sha256'])==64 and all(c in '0123456789abcdef' for c in row['sha256']) and 0<=row['bytes']<=1048576
  if row['tracking']=='tracked':assert row['index_mode'] in ['100644','100755'] and len(row['index_blob'])==40
  else:assert 'index_blob' not in row
 assert report['repository_history_exposure'] is True and report['independent_review_complete'] is report['task_accepted'] is False
 a=json.loads((e/'assessment.json').read_text());assert a['prior_graph_seal_verified'] is True and a['independent_provenance_review'] is a['task_accepted'] is a['product_edits'] is a['native_acquisition'] is False and a['revised_counts']==report['counts']
 return {'files':159,'scope_correction_retained':True,'handoff_eligible':0,'independent_review_complete':False,'task_accepted':False}
