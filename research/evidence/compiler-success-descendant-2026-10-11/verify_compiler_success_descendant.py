import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 failure=json.loads((e/'harness-failure.json').read_text());assert failure=={'phase':'repeat-0','failure':'TypeError: cannot unpack non-iterable CompletedProcess object','producer_ran':True,'root_return_not_retained':True,'at_return_snapshot_absent':True,'child_finished':True,'process_budget_used':2,'repeat_retry':False};assert not (e/'repeat-0/wait.json').exists() and not (e/'repeat-0/at-return.bin').exists()
 counts=0;children=[]
 for name in ['repeat-0','repeat-1']:
  root=e/name;done=json.loads((root/'child-finished.json').read_text());assert done['self_terminated'] is True and type(done['pid']) is int and done['pid']>1 and done['original_parent']==done['process_group'] and done['original_parent']>1 and done['pid']!=done['original_parent'] and done['bytes']==24;children.append(done['pid']);raw=(root/'heartbeat.bin').read_bytes();assert raw==bytes(range(24));counts+=len(raw)
 root=e/'repeat-1';wait=json.loads((root/'wait.json').read_text());assert wait['root_code']==0 and type(wait['root_code']) is int and wait['root_stderr']=='' and wait['child_finished_within_bound'] is True and 0<wait['root_elapsed_seconds']<1.2;row=json.loads(wait['root_stdout']);done=json.loads((root/'child-finished.json').read_text());assert row['owns_child'] is True and row['pid']==row['process_group']==done['original_parent'] and row['child_pid']==done['pid']
 first=(root/'at-return.bin').read_bytes();later=(root/'after-return.bin').read_bytes();assert len(first)==wait['first_bytes']==1 and len(later)==wait['later_bytes']==7 and wait['final_bytes']==24 and first==bytes(range(1)) and later==bytes(range(7));counts+=len(first)+len(later);assert len(set(children))==2 and counts==56
 env=json.loads((e/'environment.json').read_text());assert hashlib.sha256((e/'sourcecache.py').read_bytes()).hexdigest()==env['sourcecache_sha256']
 return {'owned_producer_processes':4,'qualified_success_controls':1,'retained_harness_failures':1,'controlled_bytes':counts,'post_return_growth':6,'normal_success_descendant_quiescence':False,'artifact_publication_tested':False}
