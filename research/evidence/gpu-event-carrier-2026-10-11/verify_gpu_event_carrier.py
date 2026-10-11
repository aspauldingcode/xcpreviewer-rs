import base64,hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'baseline/assessment.json').read_text())['acceptance'] is False
 assert json.loads((e/'prediction.json').read_text())['parent_manifest_sha256']=='0841c787c1afff6c0da6833cb5dd78dd5f82ed02c2669e948ae09a71109c615c'
 rea=json.loads((e/'rea.json').read_text());assert rea['closed'] is True and rea['identity']['package']['version']=='6.2.0'
 def integer(x,v):assert type(x) is int and x==v
 expected=bytearray([0x5c]*16384)
 for y in range(6):expected[y*256:y*256+44]=bytes([0x77]*44)
 total=0
 for root,inspection,opened,refined in [(e/'baseline','baseline','baselineOpen',False),(e,'inspection','open',True)]:
  assert json.loads((root/'compile.json').read_text())=={'wait':0,'stdout':'','stderr':''}
  env=json.loads((root/'environment.json').read_text());assert env['machine'].strip()=='arm64' and '26.6' in env['xcode'] and '25F80' in env['sw_vers']
  assert rea[inspection]['subject']['digest']['sha256']==env['helper_sha256']==rea[opened]['result']['sha256']
  for i in range(2):
   assert json.loads((root/f'wait-{i}.json').read_text())=={'code':0,'timeout':False,'stderr':''}
   d=json.loads((root/f'result-{i}.json').read_text());assert d['device']=='Apple M1' and d['unified_memory'] is True
   a=d['archive'];assert a['error_domain']=='NSCocoaErrorDomain' and a['exception_name'] is None;integer(a['error_code'],4866);integer(a['bytes'],0)
   if refined:assert a['produced_data'] is False and d['pending_timeout'] is True
   else:integer(a['produced_data'],0);integer(d['pending_timeout'],1)
   assert d['secure_string']=='owned secure-coding control' and d['rpc_error'] is None
   for k,v in [('pending_callbacks',0),('pending_value',3),('reply_wait',0),('value_after_rpc',7),('completion_wait',0),('completion_status',4),('callbacks',1)]:integer(d[k],v)
   pid=d['pid'];assert type(pid) is int and pid>0;reply=d['reply'];assert reply['imported'] is True
   for k,v in [('pid',pid),('before',3),('wrong_event',99),('after_wrong',3),('after',7)]:integer(reply[k],v)
   for k,v in [('before',bytes([0x5c]*16384)),('after',expected)]:
    b=base64.b64decode(d[k],validate=True);assert b==v;total+=len(b)
 assert total==131072
 return {'complete_bytes':total,'native_waits':4,'scope':'same-process anonymous NSXPC; no cross-process claim'}
