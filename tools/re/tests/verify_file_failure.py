import hashlib,json
from pathlib import Path

def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text())
 assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for name,row in m['files'].items():
  p=e/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink()
  b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
 for phase,pin in [('before','933f8646b7a52f27aaf120250869629f6a9a9d9f5bb10d81c6725ca7f7f4ac73'),('after','ea1140a23b66b89513badc7166cd6f9d18357e195b6796413bb11306763129b4')]:
  assert hashlib.sha256((e/(phase+'.js')).read_bytes()).hexdigest()==pin
  assert json.loads((e/(phase+'-wait.json')).read_text())=={'code':0,'stdout':'','stderr':''}
  d=json.loads((e/phase/'result.json').read_text());assert d['phase']==phase and [c['kind'] for c in d['cases']]==['opaque','ordinary']
  for c in d['cases']:
   broken=phase=='before' and c['kind']=='opaque';error='TypeError: Cannot convert object to primitive value' if broken else None
   assert c['builds']==[0,1,2] and c['pollError']==c['verifyError']==error and c['revision']==2
   rejection={'kind':'rejected','generation':2,'error':'Unprintable builder failure' if c['kind']=='opaque' else 'Error: Owned builder failure'}
   assert [v for v in c['events'] if v['kind']=='rejected']==([] if broken else [rejection])
   assert [v['generation'] for v in c['events'] if v['kind']=='observed']==[1,2,3]
   assert [(v['generation'],v['revision']) for v in c['events'] if v['kind']=='published']==[(1,1),(3,2)]
   assert c['diagnostics']=={'retainedEvents':5 if broken else 6,'droppedEvents':0,'latest':c['events'][-1],'lastFailure':None if broken else rejection}
   assert c['finalStatus']=={'liveWorkers':0,'busy':False,'closed':True,'revision':2,'loopClosed':True,'building':False,'timers':0}
   for stage,h in [('retained','13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461'),('recovery','bd9bd4fcedf2ee4139566437f0d80f486ff048c37e7df6afe8cd4b0ae4deff62')]:
    raw=(e/phase/(c['kind']+'-'+stage+'.raw')).read_bytes();assert len(raw)==16384 and hashlib.sha256(raw).hexdigest()==h
 return {'cases':4,'full_frame_bytes':131072,'row_padding_bytes':672,'allocation_tail_bytes':127488,'opaque_diagnostic_preserved':True,'native_canvas_protocol_qualified':False}
