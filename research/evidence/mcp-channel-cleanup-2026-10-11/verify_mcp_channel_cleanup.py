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
   root=e/mode/str(i);assert json.loads((root/'wait.json').read_text())=={'code':0,'stdout':'','stderr':'','timeout':False};d=json.loads((root/'result.json').read_text());assert d['fixed'] is fixed and [x['kind'] for x in d['rows']]==['complete','before-release','after-release']
   for row in d['rows']:
    kind=row['kind'];assert row['builds']==row['closeCalls']==1
    before=row['before'];assert before['lifecycle']=={'liveWorkers':1,'busy':False,'closed':False,'revision':1,'loopClosed':False,'building':False,'timers':2};assert before['readiness']['state']=='ready' and before['frame']['allocationSha256']==hashlib.sha256(expected).hexdigest()
    closed={'liveWorkers':0,'busy':False,'closed':True,'revision':1,'loopClosed':True,'building':False,'timers':0};assert row['final']['lifecycle']==closed and row['final']['frame'] is None
    assert row['after']==(before if kind=='before-release' else row['final'])
    summary={'received':1,'writes':1,'suppressed':0,'closed':True,'reason':'input-ended'}
    if fixed:summary['cleanup']='complete' if kind=='complete' else 'failed'
    assert row['summary']==summary and json.loads(row['wire'])=={'jsonrpc':'2.0','id':1,'result':{}}
    sub=root/kind;assert set(p.name for p in sub.glob('*.raw'))==({'published.raw','retained.raw'} if kind=='before-release' else {'published.raw'})
    for p in sub.glob('*.raw'):assert p.read_bytes()==expected;total+=len(expected)
 assert total==262144
 return {'complete_bytes':total,'producer_waits':4,'close_controls':12}
