import base64,hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'baseline/assessment.json').read_text())['acceptance'] is False
 total=0;expected=bytes([0x77])*4+bytes([0xc3])*16380
 for mode,fixed in [('baseline',False),('fixed',True)]:
  root=e/mode;assert json.loads((root/'wait.json').read_text())=={'code':0,'stdout':'','stderr':'','timeout':False};d=json.loads((root/'process/result.json').read_text());assert d['fixed'] is fixed and [x['mode'] for x in d['records']]==['complete','failed']
  for row in d['records']:
   fail=row['mode']=='failed';assert row['code']==(3 if fixed and fail else 0);life=row['lifecycle'];disk=json.loads((root/'process'/row['mode']/'builds/session-lifecycle.json').read_text());assert life==disk
   assert life['channel']=={'received':4,'writes':3,'suppressed':0,'closed':True,'cleanup':'failed' if fail else 'complete','reason':'input-ended'}
   assert life['final']['frame'] is None and life['final']['lifecycle']=={'liveWorkers':0,'busy':False,'closed':True,'revision':1,'loopClosed':True,'building':False,'timers':0};assert life['builds']==life['failures']==[]
   stderr=json.loads((root/'process'/row['mode']/'stderr.txt').read_text());assert stderr=={'kind':'cleanup-failed' if fixed and fail else 'closed','channel':life['channel'],'lifecycle':life['final']['lifecycle']}
   packets=row['packets'];assert [p['id'] for p in packets]==[1,2,3] and packets[0]['result']['protocolVersion']=='2025-11-25';s=json.loads(packets[1]['result']['content'][0]['text']);assert s['lifecycle']['liveWorkers']==1 and s['frame']['revision']==1
   frame=packets[2]['result']['structuredContent'];assert frame['available'] is True and frame['frame']['descriptor']==s['frame'];b=base64.b64decode(frame['frame']['allocationBase64'],validate=True);assert b==expected;assert frame['frame']['descriptor']['allocationSha256']==hashlib.sha256(expected).hexdigest();total+=len(b)
 assert total==65536
 return {'complete_bytes':total,'actual_processes':4,'cleanup_failure_exit':3}
