import base64,hashlib,json,subprocess,shutil
from pathlib import Path

def verify(e):
 e=Path(e)
 manifest=json.loads((e/'manifest.json').read_text());assert set(manifest['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,row in manifest['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and not (e/n).is_symlink()
  b=(e/n).read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
 assert json.loads((e/'prediction.json').read_text())['parentManifestSha256']=='d279f789ae43e2402474b5026b00fb7aa74b67508a2b03124282065b64d75f78'
 # Independent constant source geometry and byte oracle, including padding/tail.
 source=(e/'fixture/1-source.swift').read_bytes();assert hashlib.sha256(source).hexdigest()=='bbd58f0f81644946a503102943ad1e4916751d9788a2cb7335fa01975deaf638'
 from reloop.primarysource import parse,expected
 oracle=expected(parse(source.decode()),64);assert oracle==(e/'fixture/1-expected.raw').read_bytes()
 count=0
 for folder,file,rejected in [('baseline','baseline-result.json',False),('runtime','result.json',True)]:
  saved=json.loads((e/file).read_text());assert saved['validClosed'] and saved['terminalNoCalls'] and saved['validStale']
  assert [x['kind'] for x in saved['outcomes']]==['diagnostic-revision','diagnostic-source','missing-source','updating-source']
  for x in saved['outcomes']:
   assert x['rejected'] is rejected and x['calls']==3 and x['retained'] is rejected
   assert base64.b64decode(x['allocationBase64'],validate=True)==oracle;count+=len(oracle)
  for _ in range(2):
   p=subprocess.run([shutil.which('node'),str(e/'control/preview_identity_control.js'),str(e/folder/'preview_consumer.js'),str(e/'fixture/result.json')],capture_output=True,timeout=3)
   assert p.returncode==0 and not p.stderr and json.loads(p.stdout)==saved
 assert count==131072
 return {'complete_bytes':count,'baseline_contradictions':4,'fixed_rejections':4}
