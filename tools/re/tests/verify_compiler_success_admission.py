import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 root=e/'survivor';result=json.loads((root/'result.json').read_text());assert result['error']=='Compiler process group remains after successful root exit' and 0<result['elapsed_seconds']<1.2 and result['child_finished'] is True and result['kill_signal_used'] is False and result['first_bytes']==1 and result['later_bytes']==7
 identity=json.loads((root/'root.json').read_text());done=json.loads((root/'child-finished.json').read_text());assert identity['owns_child'] is True and identity['pid']==identity['process_group']==done['original_parent']==done['process_group'] and identity['child_pid']==done['pid'] and done['self_terminated'] is True and done['bytes']==24 and identity['pid']>1 and identity['child_pid']>1 and identity['pid']!=identity['child_pid']
 for name,n in [('at-rejection.bin',1),('after-rejection.bin',7),('heartbeat.bin',24)]:assert (root/name).read_bytes()==bytes(range(n))
 plain=json.loads((e/'plain.json').read_text());assert plain=={'code':0,'stdout':'owned clean root\n','stderr':''}
 clang=json.loads((e/'clang.json').read_text());assert clang['code']==0 and clang['stdout']==clang['stderr']=='' and clang['object_bytes']>0 and len(clang['object_sha256'])==64 and clang['compiler_sha256']=='7def90dd8829726686213a747fc5bff1583df933dae5edc55d755479e0bfe00a'
 before=(e/'sourcecache-before.py').read_text();after=(e/'sourcecache-after.py').read_text();assert 'if code==0:' not in before and 'try:os.killpg(process.pid,0)' in after and 'else:raise RuntimeError' in after and 'Compiler process group remains after successful root exit' in after
 return {'producer_processes':4,'survivor_success_rejected':True,'clean_root_accepted':True,'real_clang_object_accepted':True,'controlled_bytes':32,'destructive_success_signal':False,'escaped_descendant_quiescence':False}
