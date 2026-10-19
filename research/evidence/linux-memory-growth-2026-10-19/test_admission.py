"""Synthetic full-byte and cleanup controls only; never starts Docker/Wasmtime."""
from pathlib import Path
import copy,tempfile,unittest
from types import SimpleNamespace
import admit as a
from predictions import NAMES,expected
from container_control import cleanup
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name);out=self.p/'owned-output';out.mkdir();rows=[]
  for name in NAMES:
   raw=expected(name);(out/(name+'.raw')).write_bytes(raw);rows.append({'stage':name,'file':name+'.raw','bytes':len(raw),'sha256':a.H(raw)})
  (out/'result.json').write_text('{}')
  self.v={'pid':1,'host_system':'Linux','architecture':'aarch64','wasmtime':'49.0.0','module_bytes':80,'imports':0,'module_min_pages':1,'module_max_pages':2,'store_memory_limit_bytes':196608,'fuel_per_call':100000,'module_sha256':'970468fb9b02b07bd628c530877571db3d2ca614f73e8498b6fdd40455b3c0c6','fresh_copy_reads':True,'js_host_view_semantics_measured':False,'browser_verified':False,'canvas_qualified':False,'product_integration':False,'rows':rows,'events':[{'phase':'zero-grow','return_value':1,'pages':1},{'phase':'positive-grow','return_value':1,'pages':2},{'phase':'host-failed-grow','error':'WasmtimeError','pages':2},{'phase':'wasm-failed-grow','return_value':-1,'pages':2}]}
 def test_positive_and_scoped_binding(self):
  v=a.rows_observed(self.p,self.v);self.assertEqual(v['independent_bytes_compared'],524288);self.assertFalse(v['js_host_view_semantics_measured']);self.assertFalse(v['canvas_qualified'])
  b=expected('initial');self.assertEqual(b[:8],bytes([17,31,62,93,7,38,69,100]));self.assertEqual(b[68:96],b'\xa5'*28)
 def test_rehashed_complete_faults(self):
  for name,offset in [('initial',68),('initial',65535),('positive-grow',65541),('wasm-failed-grow',131071)]:
   p=self.p/'owned-output'/(name+'.raw');original=p.read_bytes();raw=bytearray(original);raw[offset]^=1;p.write_bytes(raw);v=copy.deepcopy(self.v);v['rows'][NAMES.index(name)]['sha256']=a.H(raw)
   with self.assertRaises(ValueError):a.rows_observed(self.p,v)
   p.write_bytes(original)
 def test_typed_events_and_scope(self):
  for key,value in [('pid',True),('imports',False),('store_memory_limit_bytes',131072),('host_system','Darwin'),('js_host_view_semantics_measured',True)]:
   v=copy.deepcopy(self.v);v[key]=value
   with self.assertRaises(ValueError):a.rows_observed(self.p,v)
  for i,key,value in [(0,'pages',True),(1,'return_value',True),(2,'error','RangeError'),(3,'return_value',0)]:
   v=copy.deepcopy(self.v);v['events'][i][key]=value
   with self.assertRaises(ValueError):a.rows_observed(self.p,v)
 def test_cleanup_ownership_and_terminal_failures(self):
  for owner,rm,remaining,ps,accept in [('mine',0,'',0,True),(None,None,'',0,True),('other',None,'',0,False),('mine',1,'',0,False),('mine',0,'still-present',0,False),(None,None,'',1,False),(None,None,'',False,False)]:
   with self.subTest(owner=owner,rm=rm,remaining=remaining,ps=ps):
    calls=[];reports=[]
    def call(args):
     calls.append(args)
     if args[0]=='inspect':return SimpleNamespace(returncode=1 if owner is None else 0,stdout=owner or '')
     if args[0]=='rm':return SimpleNamespace(returncode=rm,stdout='')
     return SimpleNamespace(returncode=ps,stdout=remaining)
    if accept:cleanup(call,{'name':'owned','owner':'mine'},reports.append)
    else:
     with self.assertRaises(ValueError):cleanup(call,{'name':'owned','owner':'mine'},reports.append)
    if owner!='mine':self.assertFalse(any(c[0]=='rm' for c in calls))
    self.assertTrue(reports)
if __name__=='__main__':unittest.main()
