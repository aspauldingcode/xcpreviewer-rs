import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 a=json.loads((e/'adoption.json').read_text());anchor='a7be4b7c9d6e0aa1a0af7d151636335fe68418787e821d073323d304303f4c15';assert a['task']==a['experiment_id']=='primary-live-wasm-swap' and a['run_id']=='20261011T093849Z-primary-live-wasm-swap-6bc05646' and a['manifest_sha256']==anchor and a['delivery_review']=='review-pending' and a['scope']=='research-only'
 assert hashlib.sha256((e/'reference-manifest.json').read_bytes()).hexdigest()==anchor
 spec=json.loads((e/'reference-experiment.json').read_text());hash_=hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert hash_==a['experiment_hash']=='11646ec7232ac3bd5da4adfa073accebb8c9417d500f10cf04df12b5afb66618'
 check=a['verification'];assert check['valid'] is True and check['recomputed_verdict']=='supports' and check['delivery_review']=='review-pending';integrity=check['integrity'];assert integrity['valid'] is True and integrity['external_anchor_matches'] is True and integrity['frozen_sources_unchanged'] is True and integrity['manifest_sha256']==anchor
 expected={x['path']:x['equals'] for x in spec['checks']};rows=check['checks'];assert len(rows)==len(expected)==88 and {x['path'] for x in rows}==set(expected)
 for x in rows:assert x['passed'] is True and x['present'] is True and x['expected']==x['actual']==expected[x['path']] and type(x['actual']) is type(expected[x['path']])
 f=json.loads((e/'frontier.json').read_text());assert f['candidates']==[] and f['all_milestones_complete'] is False and f['delivery_review']=='review-pending' and f['execution_started'] is False
 return {'fresh_declared_checks':88,'new_producer_executions':0,'milestones_complete':False}
