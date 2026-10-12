import hashlib,json
from pathlib import Path
EXPECTATIONS={'0': '13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461', '1': '44479be92b6b825d287fc9dd89edc4e4a416655463be83399ce4a0316819da29', '2': 'bd9bd4fcedf2ee4139566437f0d80f486ff048c37e7df6afe8cd4b0ae4deff62'}
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 expected={int(i):(e/'expectations'/(i+'.raw')).read_bytes() for i in EXPECTATIONS}
 for i,raw in expected.items():assert len(raw)==16384 and hashlib.sha256(raw).hexdigest()==EXPECTATIONS[str(i)]
 assert expected[0]!=expected[1] and expected[0]!=expected[2]
 fixtures=json.loads((e/'fixtures.json').read_text());assert len(fixtures)==3
 for row in fixtures:assert row['config']['width']==13 and row['config']['height']==7 and row['stride']==64
 rows=json.loads((e/'results.json').read_text());assert len(rows)==8 and {(r['phase'],r['mode']) for r in rows}=={(p,m) for p in ['before','after'] for m in ['valid','invalid','missing','refresh']};total=0
 for r in rows:
  after=r['phase']=='after';mode=r['mode'];index=2 if mode=='valid' else 1 if mode=='refresh' else 0;accepted=2 if index else 1;assert r['cancelledBeforeManualRelease'] is after and r['manuallyReleased'] is (not after) and r['aborts']==int(after) and r['accepted']==accepted and r['initialRevision']==1 and r['finalRevision']==accepted and r['expectedIndex']==index
  status=r['finalStatus'];assert status=={'liveWorkers':0,'busy':False,'closed':True,'revision':accepted,'loopClosed':True,'building':False,'timers':0}
  events=r['events'];pub=[x for x in events if x['kind']=='published'];reject=[x for x in events if x['kind']=='rejected'];observed=[x for x in events if x['kind']=='observed'];assert len(pub)==accepted and len(reject)==1 and reject[0]['generation']==2 and len(observed)==(3 if index else 2)
  assert ('Owned superseded build aborted' if after else 'Stale or foreign build ticket') in reject[0]['error'] and pub[0]['generation']==1 and pub[0]['sourceSha256']==fixtures[0]['source_sha256'] and all(x['generation']!=2 for x in pub)
  if index:assert pub[-1]['generation']==3 and pub[-1]['sourceSha256']==fixtures[index]['source_sha256']
  if mode in ['invalid','missing']:assert any(x['kind']==('invalid-source' if mode=='invalid' else 'unavailable-source') for x in events)
  base=e/(r['phase']+'-'+mode);baseline=(base/'baseline.raw').read_bytes();final=(base/'final.raw').read_bytes();assert baseline==expected[0] and final==expected[index];total+=len(baseline)+len(final)
 assert total==262144
 scope=json.loads((e/'scope.json').read_text());assert scope=={'native_canvas_qualified':False,'fresh_compilation':False,'builder_requires_cooperative_abort_settlement':True,'sequences':8,'allocations':16,'controlled_bytes':262144,'padding_bytes':1344,'unused_tail_bytes':254976}
 env=json.loads((e/'environment.json').read_text());assert env['node']['version']=='v24.19.0' and env['node']['sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e' and env['corpus_manifest_sha256']=='c53084d90de41c1e42cb8c17a38cf3b70e4fa0e6551a5937a4de7d536272e4ac' and env['budgets']=={'node_seconds':20,'corpus_source_bytes':4096,'snapshot_bytes':16384,'control_sequences':8}
 assert (e/'control.stderr').read_bytes()==b''
 return {'sequences':8,'allocations':16,'controlled_bytes':total,'padding_bytes':1344,'unused_tail_bytes':254976,'cooperative_supersession_cancel_verified':True,'native_canvas_qualified':False}
