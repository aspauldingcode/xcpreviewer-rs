import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'baseline/assessment.json').read_text())['acceptance'] is False
 for mode in ['baseline','fixed']:
  w=json.loads((e/'retained-harness-failure'/mode/'0/wait.json').read_text());assert w['code']==1 and not w['timeout'] and 'Preview tool failed' in w['stderr']
 total=0
 for mode,fixed in [('baseline',False),('fixed',True)]:
  root=e/mode/'0';assert json.loads((root/'wait.json').read_text())=={'code':0,'stderr':'','stdout':'','timeout':False}
  d=json.loads((root/'result.json').read_text());assert d['fixed'] is fixed and d['builds']==2 and d['quarantine_calls']==2
  s=d['raw_status'];assert s['lifecycle']['liveWorkers']==0 and s['lifecycle']['revision']==1 and s['frame']['stride']==64
  assert s['readiness']['state']==('stale' if fixed else 'ready');assert (d['error'] is None) is fixed
  if fixed:assert d['states'][0]==s
  a=d['states'][-1];assert a['readiness']['state']=='ready' and a['lifecycle']['liveWorkers']==1 and a['frame']['revision']==2 and a['frame']['generation']==2
  assert a['frame']['sourceSha256']==s['frame']['sourceSha256'] and a['frame']['moduleSha256']!=s['frame']['moduleSha256']
  assert d['final']==d['consumer_final'];c=d['final'];assert c['frame'] is None and c['readiness']['state']=='closed' and c['lifecycle']=={'liveWorkers':0,'busy':False,'closed':True,'revision':2,'loopClosed':True,'building':False,'timers':0}
  names=[p['name'] for p in d['packets']];assert names==['start','status','frame','status','frame','status',('status' if fixed else 'frame'),'refresh','status','frame','status','close','status','frame','status']
  for name in ['first.raw','retained.raw','recovered.raw']:
   b=(root/name).read_bytes();expected=bytes([0x77])*4+bytes([0xc3])*16380 if name=='recovered.raw' else bytes([0xc3])*16384;assert b==expected;total+=len(b)
  assert hashlib.sha256((root/'first.raw').read_bytes()).hexdigest()==s['frame']['allocationSha256'];assert hashlib.sha256((root/'recovered.raw').read_bytes()).hexdigest()==a['frame']['allocationSha256']
 assert total==98304
 return {'complete_bytes':total,'successful_waits':2,'retained_harness_failures':2}
