import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 wait=json.loads((e/'wait.json').read_text());assert wait['code']==0 and type(wait['code']) is int and wait['stdout']==wait['stderr']=='' and wait['finished_bytes']==8 and (e/'child/finished.bin').read_bytes()==b'finished';spawn=wait['spawn'];ready=json.loads((e/'child/ready.json').read_text());assert spawn['ready']==ready and spawn['popen_pid']==ready['pid']==spawn['popen_group']==ready['group'] and spawn['controller_pid']==ready['parent'] and spawn['controller_pid']!=ready['pid']
 env=json.loads((e/'environment.json').read_text());assert env['observer_subprocesses']==4 and env['signal_operations']==0 and env['observer_binary_sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5';samples=json.loads((e/'samples.json').read_text());assert [s['label'] for s in samples]==['caller-0','caller-1','child-0','child-1'];births={}
 for sample in samples:
  expected=sample['expected'];target=sample['target'];assert sample['error'] is None and type(target) is int and target==expected['pid'] and 0<sample['elapsed_seconds']<2;rows=sample['rows'];assert str(target) in rows;row=rows[str(target)];identity=row['identity'];assert row['parent']==expected['parent'] and row['group']==expected['group'] and row['state']=='L' and len(identity)==3 and all(type(x) is int and x>=0 for x in identity[:2]) and identity[2]==expected['executable']
  if target in births:assert births[target]==identity
  else:births[target]=identity
  if sample['label'].startswith('caller'):assert target==spawn['controller_pid']
  else:assert target==ready['pid'] and expected==ready and set(rows)=={str(target)}
  for pid,extra in rows.items():
   if pid!=str(target):assert extra['parent']==target and extra['group']==expected['group'] and extra['identity'][2]==env['observer_binary']
 assert len(births)==2;rea=json.loads((e/'rea-status.json').read_text());assert rea['server_identity']['server']['version']=='6.2.0'
 return {'stable_caller_samples':2,'stable_child_samples':2,'independent_parent_group_dyld_checks':4,'child_popen_identity_matches':True,'controlled_bytes':8,'native_subprocesses':5,'startup_observer_qualified':False,'signal_permission_tested':False}
