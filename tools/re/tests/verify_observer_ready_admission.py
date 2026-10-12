import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 samples=json.loads((e/'samples.json').read_text());env=json.loads((e/'environment.json').read_text());assert env['observer_subprocesses']==len(samples)==20 and env['retirement_observer_subprocesses']==1 and env['native_subprocesses']==24 and env['observer_binary_sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5';births={};total=0;roots=[];last_child=None
 for mode in ['detached','clean']:
  root=e/mode;ready=json.loads((root/'ready.json').read_text());result=json.loads((root/'result.json').read_text());pid=ready['pid'];roots.append(pid);assert result['mode']==mode and result['root_pid']==pid==ready['group'] and result['root_exit_code']==0 and type(result['root_exit_code']) is int and 0<result['elapsed_seconds']<3
  selected=[s for s in samples if s['mode']==mode];assert len(selected)==10 and selected[0]['roots']==[] and selected[0]['rows']=={} and selected[-1]['roots']==[]
  for sample in selected:
   assert 0<sample['elapsed_seconds']<2
   if sample['roots']:
    assert sample['roots']==[pid] and sample['ready']==ready;row=sample['rows'][str(pid)];assert row['parent']==ready['parent'] and row['group']==pid and row['state']=='L' and row['identity'][2]==ready['executable']
   for key,row in sample['rows'].items():
    identity=row['identity'];assert row['pid']==int(key) and len(identity)==3 and all(type(x) is int and x>=0 for x in identity[:2])
    if key in births:assert births[key]==identity
    else:births[key]=identity
  if mode=='detached':
   child=ready['child_pid'];assert type(child) is int and child!=pid and str(child) in selected[-1]['known'];last=selected[-1]['rows'][str(child)];assert last['state']=='L' and last['group']==child and last['parent']!=pid and last['identity']==selected[-1]['known'][str(child)];assert any(s['roots'] and s['rows'].get(str(child),{}).get('parent')==pid for s in selected)
   assert result['code'] is None and result['stdout'] is None and result['stderr'] is None and result['error']=='Observed compiler descendants remain after successful root exit' and result['child_finished'] is True and 0<result['first_bytes']<result['later_bytes']<32
   done=json.loads((root/'child-finished.json').read_text());assert done=={'pid':child,'original_parent':pid,'group':child,'bytes':32,'self_terminated':True}
   for name,n in [('at-rejection.bin',result['first_bytes']),('after-rejection.bin',result['later_bytes']),('heartbeat.bin',32)]:assert (root/name).read_bytes()==bytes(range(n));total+=n
   last_child=child
  else:assert ready['child_pid'] is None and result['code']==0 and result['error'] is None and result['stdout']=='owned observed root\n' and result['stderr']=='' and selected[-1]['rows']=={};total+=len(result['stdout'].encode())
 assert len(set(roots+[last_child]))==3 and total==76
 signals=json.loads((e/'signals.json').read_text());assert signals==[{'mode':'clean','pid':roots[1],'signal':0,'outcome':'absent'}]
 retirement=json.loads((e/'retirement.json').read_text());assert retirement['child_pid']==last_child and retirement['known_identity']==births[str(last_child)] and retirement['live_owned_child'] is False and 0<retirement['elapsed_seconds']<2
 for key,row in retirement['rows'].items():assert key==str(last_child) and row['state']=='Z' and row['identity']==births[key]
 rea=json.loads((e/'rea-status.json').read_text());assert rea['server_identity']['server']['version']=='6.2.0'
 return {'producer_roles':3,'observer_helpers':21,'native_subprocesses':24,'controlled_bytes':total,'ready_gated_post_root_rejection_verified':True,'clean_ready_root_admitted':True,'destructive_signals':0,'generic_startup_qualified':False}
