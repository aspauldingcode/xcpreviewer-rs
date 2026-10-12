import hashlib,json
from pathlib import Path
GOLDEN='13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461'
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 expected=(e/'expected.raw').read_bytes();assert len(expected)==16384 and hashlib.sha256(expected).hexdigest()==GOLDEN
 rows=json.loads((e/'results.json').read_text());assert len(rows)==8 and {(r['phase'],r['mode']) for r in rows}=={(p,m) for p in ['before','after'] for m in ['valid','invalid','missing','refresh']};total=0
 for r in rows:
  assert r['observedError']==('Source host closed' if r['phase']=='before' else None) and r['aborts']==1 and r['buildCalls']==2 and r['frameCleared'] is True
  assert r['finalStatus']=={'liveWorkers':0,'busy':False,'closed':True,'revision':1,'loopClosed':True,'building':False,'timers':0}
  events=r['events'];observed=[x for x in events if x['kind']=='observed'];pub=[x for x in events if x['kind']=='published'];reject=[x for x in events if x['kind']=='rejected'];assert len(events)==4 and [x['generation'] for x in observed]==[1,2] and len(pub)==1 and pub[0]['generation']==1 and pub[0]['revision']==1 and pub[0]['sourceSha256']==observed[0]['sourceSha256'] and observed[0]['sourceSha256']=='37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8' and observed[1]['sourceSha256']=='fedcf8a6469cface25d9f4c28c3b041b957dca31ee511960827abf86c18e990f'
  assert len(reject)==1 and reject[0]['generation']==2 and reject[0]['error']=='Error: Owned abort callback closes loop'
  frame=(e/(r['phase']+'-'+r['mode'])/'baseline.raw').read_bytes();assert frame==expected;total+=len(frame)
 assert total==131072
 scope=json.loads((e/'scope.json').read_text());assert scope['native_canvas_qualified'] is False and scope['fresh_compilation'] is False and scope['sequences']==scope['allocations']==8 and scope['controlled_bytes']==131072 and scope['padding_bytes']==672 and scope['unused_tail_bytes']==127488
 env=json.loads((e/'environment.json').read_text());assert env['node']['version']=='v24.19.0' and env['node']['sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e' and env['corpus_manifest_sha256']=='c53084d90de41c1e42cb8c17a38cf3b70e4fa0e6551a5937a4de7d536272e4ac' and env['budgets']=={'node_seconds':20,'snapshot_bytes':16384,'control_sequences':8}
 assert (e/'control.stderr').read_bytes()==b''
 return {'sequences':8,'controlled_bytes':total,'padding_bytes':672,'unused_tail_bytes':127488,'reentrant_close_respected':True,'native_canvas_qualified':False}
