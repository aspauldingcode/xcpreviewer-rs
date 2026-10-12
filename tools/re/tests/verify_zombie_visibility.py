import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 d=json.loads((e/'result.json').read_text());ready=d['ready'];root=ready['pid'];child=ready['child'];assert root!=child and ready['group']==root and ready['child_group']==child and ready['executable'].startswith('/')
 assert d['root_exit_code']==0 and type(d['root_exit_code']) is int and d['signals']==[] and d['native_subprocesses']==6 and d['zombie_row_present'] is False and d['retired_row_present'] is False
 assert d['unreaped']=={'phase':'unreaped','child':child,'status':42,'code':1,'exited':True} and d['reaped']=={'phase':'reaped','child':child,'exit_code':42,'exited':True}
 samples=json.loads((e/'samples.json').read_text());assert len(samples)==3 and [s['stage'] for s in samples]==['live','unreaped','reaped'];first=samples[0];assert first['roots']==[root] and first['known']=={} and set(first['rows'])=={str(root),str(child)}
 for pid,parent,group in [(root,ready['parent'],root),(child,root,child)]:
  row=first['rows'][str(pid)];assert row['pid']==pid and row['parent']==parent and row['group']==group and row['state']=='L';identity=row['identity'];assert len(identity)==3 and all(type(x) is int and x>=0 for x in identity[:2]) and identity[2]==ready['executable']
 for sample in samples:assert 0<sample['elapsed_seconds']<2
 for sample in samples[1:]:assert sample['roots']==[] and sample['rows']=={} and sample['known']=={str(child):first['rows'][str(child)]['identity']}
 assert (e/'child.bin').read_bytes()==bytes(range(32)) and (e/'compile.stdout').read_bytes()==b'' and (e/'compile.stderr').read_bytes()==b'' and (e/'fixture.stderr').read_bytes()==b''
 env=json.loads((e/'environment.json').read_text());assert env['helper_sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5' and env['budgets']=={'compile_seconds':10,'helper_seconds':2,'fixture_phase_seconds':4,'controller_line_seconds':3,'root_wait_seconds':3,'native_subprocesses':6}
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0'
 return {'native_subprocesses':6,'controlled_bytes':32,'unreaped_and_reaped_rows_both_absent':True,'native_matching_zombie_row_qualified':False}
