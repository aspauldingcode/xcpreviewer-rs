import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'baseline/assessment.json').read_text())['acceptance'] is False
 env=json.loads((e/'environment.json').read_text());assert env['node'] and env['v8'] and env['platform']=='darwin' and env['arch']=='arm64'
 total=0
 for mode,fixed in [('baseline',False),('fixed',True)]:
  for i in range(2):
   root=e/mode/str(i);assert json.loads((root/'wait.json').read_text())=={'code':0,'stderr':'','stdout':'','timeout':False}
   d=json.loads((root/'result.json').read_text());assert d['fixed'] is fixed and 'deadline' in d['first_error'];assert ('unavailable' if fixed else 'deadline') in d['second_error']
   assert d['rows']==[{'liveWorkers':0 if fixed else 1,'busy':False,'closed':False,'revision':1}]*2+[{'liveWorkers':1,'busy':False,'closed':False,'revision':2}]
   assert d['final']=={'liveWorkers':0,'busy':False,'closed':True,'revision':2} and d['snapshot_after_close'] is None
   for name in ['first.raw','retained.raw','recovered.raw']:
    b=(root/name).read_bytes();assert b==bytes([0xc3])*16384;total+=len(b)
 assert total==196608
 return {'complete_bytes':total,'actual_waits':4}
