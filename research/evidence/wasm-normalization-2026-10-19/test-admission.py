from pathlib import Path
import unittest,tempfile,json,hashlib,shutil
from admit import admit,METHODS
from predictions import readback
from build import module
P=Path(__file__).resolve().parent
class Admission(unittest.TestCase):
 def fixture(self,p):
  (p/'probe.wasm').write_bytes(module());(p/'owned-output').mkdir();rows=[]
  for method in METHODS:
   raw=readback('multiply' if method.endswith('multiply') else 'divide');name=method+'.raw';(p/'owned-output'/name).write_bytes(raw);rows.append({'method':method,'file':name,'allocation_bytes':16384,'sha256':hashlib.sha256(raw).hexdigest()})
  out={'pid':12345,'environment':dict(node='synthetic',v8='synthetic',platform='darwin',arch='arm64'),'module_sha256':hashlib.sha256(module()).hexdigest(),'module_bytes':81,'sections':[1,3,7,10],'imports':[],'exports':[dict(name='multiplyBits',kind='function'),dict(name='divideBits',kind='function')],'invalid_inputs':[dict(label=x,rejected=True,dispatch_delta=0) for x in ['negative','large','fraction','nonfinite','boolean']],'scalar_dispatches':9216,'rows':rows,**{k:False for k in ['native_UI_execution','product_integration','second_runtime_verified','non_Apple_OS_verified']}}
  (p/'execution.json').write_text(json.dumps({'exit':0,'stderr':'','stdout':json.dumps(out),'executions':1,'deadline_utc':'2026-10-19T09:35:00Z','completed_at':'2026-10-19T09:25:00+00:00'}))
 def test_positive(self):
  with tempfile.TemporaryDirectory() as d:p=Path(d);self.fixture(p);self.assertEqual(admit(p)['full_bytes_compared'],65536)
 def test_resealed_region_faults(self):
  for offset in [0,4096,16383]:
   with self.subTest(offset=offset),tempfile.TemporaryDirectory() as d:
    p=Path(d);self.fixture(p);q=p/'owned-output/wasm-multiply.raw';raw=bytearray(q.read_bytes());raw[offset]^=1;q.write_bytes(raw);f=p/'execution.json';o=json.loads(f.read_text());v=json.loads(o['stdout']);v['rows'][0]['sha256']=hashlib.sha256(raw).hexdigest();o['stdout']=json.dumps(v);f.write_text(json.dumps(o))
    with self.assertRaises(ValueError):admit(p)
 def test_contract_faults(self):
  for fault in ['module','imports','memory_section','float_section','dispatch','invalid','cross_platform_claim','boolean_exit']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
    p=Path(d);self.fixture(p);f=p/'execution.json';o=json.loads(f.read_text());v=json.loads(o['stdout'])
    if fault=='module':(p/'probe.wasm').write_bytes(module()+b'\0')
    if fault=='imports':v['imports']=[{'module':'host','name':'write','kind':'function'}]
    if fault=='memory_section':v['sections']=[1,3,5,7,10]
    if fault=='float_section':v['sections']=[1.0,3,7,10]
    if fault=='dispatch':v['scalar_dispatches']-=1
    if fault=='invalid':v['invalid_inputs'][0]['dispatch_delta']=1
    if fault=='cross_platform_claim':v['non_Apple_OS_verified']=True
    if fault=='boolean_exit':o['exit']=False
    o['stdout']=json.dumps(v);f.write_text(json.dumps(o))
    with self.assertRaises(ValueError):admit(p)
if __name__=='__main__':unittest.main()
