import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 total=0;roots=[];children=[]
 for name in ['group-only','observed']:
  root=e/name;result=json.loads((root/'result.json').read_text());identity=json.loads((root/'root.json').read_text());done=json.loads((root/'child-finished.json').read_text());assert result['finished'] is True and result['destructive_success_signal'] is False and done['self_terminated'] is True and done['bytes']==32 and identity['pid']==identity['group']==done['original_parent'] and identity['child_pid']==done['pid']==done['group'] and identity['pid']!=identity['child_pid'];roots.append(identity['pid']);children.append(identity['child_pid'])
  if name=='group-only':assert result['code']==0 and result['error'] is None and result['stderr']=='' and json.loads(result['stdout'])==identity
  else:assert result['code'] is None and result['stdout'] is None and result['stderr'] is None and result['error']=='Compiler observed lifetime identity changed'
  assert 0<result['elapsed_seconds']<1.6 and 0<result['first_bytes']<result['later_bytes']<32
  for file,n in [('at-return.bin',result['first_bytes']),('after-return.bin',result['later_bytes']),('heartbeat.bin',32)]:raw=(root/file).read_bytes();assert raw==bytes(range(n));total+=len(raw)
 assert len(set(roots+children))==4 and total==100
 samples=json.loads((e/'observer-samples.json').read_text());assert len(samples)==3 and samples[0]['roots']==[] and samples[0]['rows']=={}
 root=roots[1];child=children[1];first=samples[1]['rows'][str(root)]['identity'];second=samples[2]['rows'][str(root)]['identity'];assert first[:2]==second[:2] and first[2]!=second[2] and samples[1]['roots']==samples[2]['roots']==[root];row=samples[2]['rows'][str(child)];assert row['parent']==root and row['group']==child and row['state']=='L'
 failure=json.loads((e/'retained-failure.json').read_text());assert failure['qualified_observed_success_admission'] is False and failure['budget_exhausted'] is True and failure['producer_retry'] is False
 env=json.loads((e/'environment.json').read_text());assert env['observer_samples']==3 and env['total_native_processes']==7;rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==env['observer_binary_sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5' and rea['identity']['result']['architecture']=='arm64' and rea['closed']['result'] is None
 return {'controlled_bytes':total,'producer_processes':4,'observer_processes':3,'group_only_escape_counterexample':True,'retained_root_exec_failure':True,'native_post_root_observer_qualified':False}
