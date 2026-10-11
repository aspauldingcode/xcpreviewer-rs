import base64,hashlib,json,shutil,subprocess
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'prediction.json').read_text())['parentManifestSha256']=='476942f9568e9cae06dfdc15d908bce871fa347122a245f55365ea4325ed757a'
 assert json.loads((e/'baseline-assessment.json').read_text())['acceptance'] is False
 assert json.loads((e/'retained-candidate-failure/assessment.json').read_text())['actual_wait']==1 and json.loads((e/'retained-candidate-failure/assessment.json').read_text())['acceptance'] is False
 source=(e/'fixture/1-source.swift').read_bytes();assert hashlib.sha256(source).hexdigest()=='bbd58f0f81644946a503102943ad1e4916751d9788a2cb7335fa01975deaf638'
 from reloop.primarysource import parse,expected
 oracle=expected(parse(source.decode()),64);assert oracle==(e/'fixture/1-expected.raw').read_bytes();count=0
 for runtime,result,fixed in [('baseline','baseline-result.json',False),('runtime','result.json',True)]:
  assert json.loads((e/(runtime+'-wait.json')).read_text())=={'code':0,'timeout':False,'stderr':''}
  d=json.loads((e/result).read_text());assert d['validClosed'] is True and d['validStale'] is True and d['terminalNoCalls'] is True
  assert [x['revision'] for x in d['outcomes']]==[0,1]
  for x in d['outcomes']:
   assert x['rejected'] is fixed and x['retained'] is fixed and type(x['calls']) is int and x['calls']==3
   assert x['afterRevision']==(2 if fixed else x['revision']) and x['recoveryRevision']==(2 if fixed else x['revision'])
   assert x['afterClosed'] is (not fixed) and x['recoveryClosed'] is (not fixed) and x['recoveryCalls']==(3 if fixed else 0)
   for key in ['beforeAllocationBase64','afterAllocationBase64','recoveryAllocationBase64']:
    if fixed or key=='beforeAllocationBase64':assert base64.b64decode(x[key],validate=True)==oracle;count+=len(oracle)
    else:assert x[key] is None
  assert base64.b64decode(d['validAllocationBase64'],validate=True)==oracle;count+=len(oracle)
  for _ in range(2):
   p=subprocess.run([shutil.which('node'),str(e/'control/preview_close_revision_control.js'),str(e/runtime/'preview_consumer.js'),str(e/'fixture/result.json')],capture_output=True,timeout=3)
   assert p.returncode==0 and not p.stderr and json.loads(p.stdout)==d
 assert count==163840
 return {'complete_bytes':count,'baseline_contradictions':2,'fixed_rejections':2,'fixed_recoveries':2}
