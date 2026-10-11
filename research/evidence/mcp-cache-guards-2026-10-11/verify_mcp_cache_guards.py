import hashlib,json
from pathlib import Path
KINDS=['sourceSha256','moduleSha256','allocationSha256','generation','revision','width','stride','renderedBytes','lifecycle','diagnostic','unstable','cold','valid','retry']
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 for sub,mutant in [('0',False),('1',False),('mutants/lifecycle/process',True)]:
  root=e/sub;assert json.loads((root/'wait.json').read_text())=={'code':0,'stdout':'','stderr':'','timeout':False};d=json.loads((root/'result.json').read_text());assert d['bytes']==212992 and [x['kind'] for x in d['rows']]==KINDS
  for row in d['rows']:
   k=row['kind'];calls=['preview_status'];error='Unavailable publication identity changed';accepted={'revision':1,'state':'ready'}
   if k=='lifecycle':calls*=2;error='Lifecycle revision rollback' if mutant else 'Lifecycle publication mismatch'
   if k=='diagnostic':calls*=2;error='Diagnostic publication mismatch'
   if k=='unstable':calls*=4;error='Preview changed during bounded sample'
   if k=='cold':calls=['preview_status','preview_frame'];error='Preview tool failed';accepted=None
   if k=='valid':calls*=2;error=None;accepted={'revision':1,'state':'stale'}
   if k=='retry':calls=['preview_status']*3+['preview_frame','preview_status'];error=None;accepted={'revision':2,'state':'ready'}
   assert row['calls']==calls and row['accepted']==accepted
   assert row['error'] is None if error is None else isinstance(row['error'],str) and error in row['error']
 w=json.loads((e/'mutants/diagnostic/process/wait.json').read_text());assert w['code']==1 and not w['timeout'] and 'AssertionError' in w['stderr'];assert not (e/'mutants/diagnostic/process/result.json').exists()
 total=0;count=0
 for p in e.rglob('*.raw'):
  expected=bytes([0x77])*4+bytes([0xc3])*16380 if p.name=='retry.raw' else bytes([0xc3])*16384;assert p.read_bytes()==expected;total+=len(expected);count+=1
 assert count==48 and total==786432
 assert json.loads((e/'mutants/assessment.json').read_text())['acceptance'] is False
 return {'complete_bytes':total,'histories':28,'source_mutants':2}
