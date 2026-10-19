import unittest,tempfile,json,copy
from pathlib import Path
from admit import check_output,METHODS
from predictions import readback
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name);(self.p/'owned-documents').mkdir()
  self.o={'engine':'public JavaScriptCore JSContext','pid':123,'environment':dict(framework_path='/System/Library/Frameworks/JavaScriptCore.framework',framework_identifier='com.apple.JavaScriptCore',framework_version='test-model',system='Darwin',release='test',machine='arm64',os_version='test-model'),'native_UI_execution':False,'product_integration':False,'non_Apple_OS_verified':False,'canvas_qualified':False,'status':'supported','metadata_json_order_matches':True,'export_key_order':[['name','kind'],['name','kind']],'module_bytes':81,'sections':[1,3,7,10],'imports':[],'exports':[{'name':'multiplyBits','kind':'function'},{'name':'divideBits','kind':'function'}],'scalar_dispatches':9216,'invalid_inputs':[{'label':x,'rejected':True,'dispatch_delta':0} for x in ['negative','large','fraction','nonfinite','boolean']],'rows':[{'method':m,'file':m+'.raw','allocation_bytes':16384} for m in METHODS]}
  for m in METHODS:(self.p/'owned-documents'/(m+'.raw')).write_bytes(readback(m.rsplit('-',1)[1]))
 def tearDown(self):self.t.cleanup()
 def test_positive(self):self.assertEqual(check_output(self.o,self.p)['full_bytes_compared'],65536)
 def test_pixel_padding_tail(self):
  q=self.p/'owned-documents'/'wasm-multiply.raw';raw=q.read_bytes()
  for offset in [0,4096,12480,16383]:
   with self.subTest(offset=offset):
    b=bytearray(raw);b[offset]^=1;q.write_bytes(b)
    with self.assertRaises(ValueError):check_output(self.o,self.p)
    q.write_bytes(raw)
 def test_contract(self):
  for key,value in [('pid',True),('module_bytes',81.0),('sections',[True,3,7,10]),('imports',[{}]),('scalar_dispatches',9215),('canvas_qualified',True),('status','unsupported')]:
   with self.subTest(key=key):
    o=copy.deepcopy(self.o);o[key]=value
    with self.assertRaises(ValueError):check_output(o,self.p)
 def test_unsupported(self):
  for q in (self.p/'owned-documents').iterdir():q.unlink()
  o=copy.deepcopy(self.o);o.update(status='unsupported',webassembly_type='undefined',rows=[],scalar_dispatches=0)
  self.assertFalse(check_output(o,self.p)['second_engine_scalar_conformance'])
  o['scalar_dispatches']=True
  with self.assertRaises(ValueError):check_output(o,self.p)
if __name__=='__main__':unittest.main()
