import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'baseline/assessment.json').read_text())['acceptance'] is False
 total=0;expected=bytes([0x77])*4+bytes([0xc3])*16380
 for mode,fixed in [('baseline',False),('fixed',True)]:
  for i in range(2):
   root=e/mode/str(i);assert json.loads((root/'wait.json').read_text())=={'code':0,'stdout':'','stderr':'','timeout':False};d=json.loads((root/'result.json').read_text());assert d['fixed'] is fixed and d['ids']==256 and d['builds']==1
   before=d['before'];assert before==d['atCap'];assert before['lifecycle']=={'liveWorkers':1,'busy':False,'closed':False,'revision':1,'loopClosed':False,'building':False,'timers':2};assert before['readiness']['state']=='ready' and before['frame']['revision']==1 and before['frame']['stride']==64
   assert before['frame']['allocationSha256']==hashlib.sha256(expected).hexdigest()
   for name,ident in [('limited',257),('repeated',258)]:assert d[name]=={'jsonrpc':'2.0','id':ident,'error':{'code':-32000,'message':'Session request limit'}}
   closed={'liveWorkers':0,'busy':False,'closed':True,'revision':1,'loopClosed':True,'building':False,'timers':0}
   assert d['final']['lifecycle']==closed and d['final']['frame'] is None
   assert d['after']==(d['final'] if fixed else before)
   assert d['cleanupFailure']=={'jsonrpc':'2.0','id':256,'error':{'code':-32000,'message':'Session request limit; cleanup failed' if fixed else 'Session request limit'}}
   for p in root.glob('*.raw'):assert p.read_bytes()==expected;total+=len(expected)
   assert set(p.name for p in root.glob('*.raw'))==({'published.raw'} if fixed else {'published.raw','retained.raw'})
 assert total==98304
 return {'complete_bytes':total,'producer_waits':4,'request_id_bound':256}
