import hashlib,json
from pathlib import Path

def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text())
 assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for name,row in m['files'].items():
  p=e/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink()
  b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
 pins=['0747cd8c9fa9f7437e4533099cc18124cbdb4e5386d243a1dbf0b5529fd1f201','933f8646b7a52f27aaf120250869629f6a9a9d9f5bb10d81c6725ca7f7f4ac73']
 hashes=['37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8','fedcf8a6469cface25d9f4c28c3b041b957dca31ee511960827abf86c18e990f','d11ab052939b2b5b4b88e58fb0ee1e210772d2a756083bfd6f9d8f34452818cc']
 gold=['13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461',None,'bd9bd4fcedf2ee4139566437f0d80f486ff048c37e7df6afe8cd4b0ae4deff62']
 for phase,pin in zip(['before','after'],pins):
  assert hashlib.sha256((e/(phase+'.js')).read_bytes()).hexdigest()==pin
  for mode in ['poll','refresh']:
   root=e/(phase+'-'+mode);d=json.loads((root/'result.json').read_text());winner=0 if phase=='before' else 2;generation=4 if phase=='before' else 3
   assert json.loads((e/(phase+'-'+mode+'-wait.json')).read_text())=={'code':0,'stdout':'','stderr':''}
   assert d['phase']==phase and d['mode']==mode and d['builds']==[0,1,winner] and d['winner']==winner and d['revision']==2 and d['sourceOnDisk']==2 and d['aborts']==d['nested']==1
   observed=[x for x in d['events'] if x['kind']=='observed'];assert [x['sourceSha256'] for x in observed]==[hashes[i] for i in ([0,1,2,0] if phase=='before' else [0,1,2])]
   assert [x['generation'] for x in observed]==list(range(1,generation+1))
   assert [x for x in d['events'] if x['kind']=='published']==[{'kind':'published','generation':1,'revision':1,'sourceSha256':hashes[0]},{'kind':'published','generation':generation,'revision':2,'sourceSha256':hashes[winner]}]
   assert [x for x in d['events'] if x['kind']=='rejected']==[{'kind':'rejected','generation':2,'error':'Error: Owned superseded build'}]
   assert d['finalStatus']=={'liveWorkers':0,'busy':False,'closed':True,'revision':2,'loopClosed':True,'building':False,'timers':0}
   raw=(root/'frame.raw').read_bytes();assert len(raw)==16384 and hashlib.sha256(raw).hexdigest()==gold[winner]
   assert (root/'owned.swift').read_bytes()==(e/'source-2.swift').read_bytes()
 for i,h in enumerate(hashes):assert hashlib.sha256((e/('source-'+str(i)+'.swift')).read_bytes()).hexdigest()==h
 assert json.loads((e/'environment.json').read_text())['node_sha256']=='768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e'
 return {'cases':4,'full_frame_bytes':65536,'row_padding_bytes':336,'allocation_tail_bytes':63744,'latest_nested_source_wins':True,'native_canvas_refresh_qualified':False}
