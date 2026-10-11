import base64,hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'baseline/assessment.json').read_text())['acceptance'] is False
 total=0;pids=[];expected=bytes([0x77])*4+bytes([0xc3])*16380
 for mode,fixed in [('baseline',False),('fixed',True)]:
  root=e/mode;assert json.loads((root/'wait.json').read_text())=={'code':0,'stdout':'','stderr':'','timeout':False};d=json.loads((root/'process/result.json').read_text());assert d['fixed'] is fixed and [x['mode'] for x in d['records']]==['complete','hung']
  for row in d['records']:
   hung=row['mode']=='hung';assert row['code']==((4 if fixed else -9) if hung else 0);assert row['wait_timeout'] is (hung and not fixed);assert row['process_reaped'] is True and isinstance(row['pid'],int) and row['pid']>0;pids.append(row['pid'])
   sub=root/'process'/row['mode'];artifact=row['artifact'];normal=sub/'builds/session-lifecycle.json';timeout=sub/'builds/shutdown-timeout.json';stderr=(sub/'stderr.txt').read_text()
   if not hung:
    assert artifact==json.loads(normal.read_text()) and not timeout.exists();assert artifact['channel']=={'received':4,'writes':3,'suppressed':0,'closed':True,'cleanup':'complete','reason':'input-ended'};assert artifact['final']['frame'] is None and artifact['final']['lifecycle']=={'liveWorkers':0,'busy':False,'closed':True,'revision':1,'loopClosed':True,'building':False,'timers':0};assert json.loads(stderr)=={'kind':'closed','channel':artifact['channel'],'lifecycle':artifact['final']['lifecycle']}
   elif fixed:
    assert not normal.exists() and artifact==json.loads(timeout.read_text())==json.loads(stderr);assert artifact['kind']=='shutdown-timeout' and artifact['deadlineMs']==500 and artifact['graceMs']==1000 and artifact['cleanup']=='unknown';assert artifact['final']['lifecycle']=={'liveWorkers':1,'busy':False,'closed':False,'revision':1,'loopClosed':False,'building':False,'timers':2};assert artifact['final']['frame']['revision']==1
   else:assert artifact is None and not normal.exists() and not timeout.exists() and stderr==''
   packets=row['packets'];assert [p['id'] for p in packets]==[1,2,3];s=json.loads(packets[1]['result']['content'][0]['text']);f=packets[2]['result']['structuredContent'];assert f['available'] is True and f['frame']['descriptor']==s['frame'];b=base64.b64decode(f['frame']['allocationBase64'],validate=True);assert b==expected and f['frame']['descriptor']['allocationSha256']==hashlib.sha256(expected).hexdigest();total+=len(b)
 assert total==65536 and len(set(pids))==4
 return {'complete_bytes':total,'actual_processes':4,'watchdog_exit':4}
