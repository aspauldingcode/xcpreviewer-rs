"""Synthetic fault controls; no JavaScript/WASM execution."""
from pathlib import Path
import copy
import tempfile
import unittest
import byte_compare as a
from predictions import NAMES,expected
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name);(self.p/'owned-documents').mkdir();rows=[]
  for n in NAMES:
   b=expected(n);(self.p/'owned-documents'/(n+'.raw')).write_bytes(b);rows.append({'stage':n,'file':n+'.raw','bytes':len(b),'sha256':a.H(b)})
  detached=lambda name,size:{'phase':name,'return_value':1,'new_buffer_bytes':size,'buffer_changed':True,'old_buffer_bytes':0,'old_view_bytes':0,'data_view_error':'TypeError','stale_read_undefined':True,'stale_write_affected_current':False}
  failed={'buffer_same':True,'view_bytes':131072,'new_buffer_bytes':131072}
  self.v={'pid':123,'module_sha256':a.MODULE,'module_bytes':80,'imports':[],'exports':[{'name':'memory','kind':'memory'},{'name':'store8','kind':'function'},{'name':'grow','kind':'function'}],'rows':rows,'events':[detached('zero-grow',65536),detached('positive-grow',131072),dict(failed,phase='js-failed-grow',error='RangeError'),dict(failed,phase='wasm-failed-grow',return_value=-1)],'browser_execution':False,'native_canvas_evidence':False,'product_integration':False}
 def test_positive_and_independent_samples(self):
  r=a.result(self.p,self.v);self.assertEqual(r['all_bytes_compared'],524288);self.assertTrue(r['zero_growth_detaches']);self.assertFalse(r['canvas_qualified'])
  b=expected('initial');self.assertEqual(b[:8],bytes([17,31,62,93,7,38,69,100]));self.assertEqual(b[68:96],b'\xa5'*28);self.assertEqual(b[480:],b'\xa5'*65056)
 def test_rehashed_complete_memory_faults(self):
  for stage,offset in [('initial',0),('initial',68),('initial',65535),('positive-grow',65541),('wasm-failed-grow',131071)]:
   with self.subTest(stage=stage,offset=offset):
    i=NAMES.index(stage);q=self.p/'owned-documents'/(stage+'.raw');original=q.read_bytes();b=bytearray(original);b[offset]^=1;q.write_bytes(b);v=copy.deepcopy(self.v);v['rows'][i]['sha256']=a.H(b)
    with self.assertRaises(ValueError):a.result(self.p,v)
    q.write_bytes(original)
 def test_event_and_typed_metadata_faults(self):
  for index,key,value in [(0,'buffer_changed',False),(0,'old_buffer_bytes',False),(0,'return_value',True),(0,'data_view_error',None),(1,'stale_write_affected_current',True),(2,'buffer_same',False),(2,'error','TypeError'),(3,'return_value',0)]:
   with self.subTest(index=index,key=key):
    v=copy.deepcopy(self.v);v['events'][index][key]=value
    with self.assertRaises(ValueError):a.result(self.p,v)
  for key,value in [('pid',True),('module_bytes',80.0),('browser_execution',True)]:
   v=copy.deepcopy(self.v);v[key]=value
   with self.assertRaises(ValueError):a.result(self.p,v)
 def test_length_path_and_inventory(self):
  for change in ['length','path','extra']:
   with self.subTest(change=change):
    v=copy.deepcopy(self.v)
    if change=='length':v['rows'][0]['bytes']=True
    elif change=='path':v['rows'][0]['file']='../initial.raw'
    else:(self.p/'owned-documents'/'extra.raw').write_bytes(b'')
    with self.assertRaises(ValueError):a.result(self.p,v)
if __name__=='__main__':unittest.main()
