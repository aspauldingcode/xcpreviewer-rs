import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 for owner in [False,True]:
  base=e/'owner-query' if owner else e;d=json.loads((base/'result.json').read_text());r=d['ready'];root=r['pid'];child=r['child'];assert root!=child and r['group']==root and r['child_group']==child and d['root_exit_code']==0 and type(d['root_exit_code']) is int and d['signals']==[] and d['native_subprocesses']==(6 if owner else 10)
  a=d['waitid' if owner else 'unreaped'];b=d['waitpid' if owner else 'reaped'];assert a=={'phase':'unreaped','child':child,'status':42,'code':1,'exited':True} and b=={'phase':'reaped','child':child,'exit_code':42,'exited':True}
  samples=json.loads((base/'samples.json').read_text());assert [s['stage'] for s in samples]==['live','unreaped','reaped'];identity=samples[0]['known'][str(child)];assert len(identity)==3 and identity[2]==r['executable'] and all(type(x) is int and x>=0 for x in identity[:2])
  for sample in samples:
   stage=sample['stage'];assert sample['known']=={str(child):identity} and sample['typed']=={str(child):{'pid':child,'expected_birth':identity[:2],'observed_birth':identity[:2] if stage=='live' else None,'status':'live' if stage=='live' else 'unavailable'}}
   if owner:
    assert 0<sample['elapsed_seconds']<2;row=sample['owner'];assert row['child']==child and row['owner_phase']==stage
    if stage=='live':assert row['query']=={'bytes':136,'pid':child,'birth':identity[:2],'state':2}
    else:assert row['query']=={'bytes':0}
   else:
    assert 0<sample['observer_elapsed_seconds']<2 and 0<sample['typed_elapsed_seconds']<2
    if stage=='live':
     assert sample['roots']==[root] and set(sample['rows'])=={str(root),str(child)};row=sample['rows'][str(child)];assert row['pid']==child and row['parent']==root and row['group']==child and row['state']=='L' and row['identity']==identity;parent=sample['rows'][str(root)];assert parent['parent']==r['parent'] and parent['group']==root and parent['state']=='L' and parent['identity'][2]==r['executable']
    else:assert sample['roots']==[] and sample['rows']=={}
  assert (base/'child.bin').read_bytes()==bytes(range(32))
  for name in ['compile.stdout','compile.stderr','fixture.stderr']:assert (base/name).read_bytes()==b''
 original=json.loads((e/'result.json').read_text());child=original['ready']['child'];identity=json.loads((e/'samples.json').read_text())[0]['known'][str(child)];wrong=json.loads((e/'wrong-birth.json').read_text());expected=[identity[0]+1,identity[1]];assert wrong['known']=={str(child):expected+[identity[2]]} and wrong['rows']=={str(child):{'pid':child,'expected_birth':expected,'observed_birth':identity[:2],'status':'reused'}} and 0<wrong['elapsed_seconds']<2
 env=json.loads((e/'environment.json').read_text());assert env['helper_sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5' and env['typed_source_sha256']==hashlib.sha256((e/'OwnedProcessRetirement.c').read_bytes()).hexdigest() and env['typed_python_sha256']==hashlib.sha256((e/'processretirement.py').read_bytes()).hexdigest() and env['budgets']['native_subprocesses']==10 and env['budgets']['helper_seconds']==2
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0' and rea['target']['sha256']==env['typed_helper_sha256'] and rea['target']['architecture']=='arm64'
 failure=json.loads((e/'retained-failure.json').read_text());assert failure['native_retirement_qualified'] is False and failure['retries_unchanged']==0 and failure['native_subprocesses']==16 and failure['controlled_bytes']==64
 return {'native_subprocesses':16,'controlled_bytes':64,'live_and_wrong_birth_qualified':True,'unreaped_retirement_qualified':False,'owning_parent_unreaped_bsd_bytes':0}
