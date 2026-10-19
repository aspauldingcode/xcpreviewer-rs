"""Synthetic marker/event faults only; never invokes the provider or a child."""
from pathlib import Path
import copy,json,tempfile,unittest
import admit as a
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name);(self.p/'owned-documents').mkdir();rows=[]
  for i,mode in enumerate(['default','stoppable']):
   d=self.p/'owned-documents'/mode;d.mkdir();pid=201+i;nonce=('a' if i==0 else 'b')*32
   for name,v in [('ready',{'pid':pid,'ppid':100,'nonce':nonce}),('term',{'pid':pid,'nonce':nonce,'signal':'SIGTERM'}),('done',{'pid':pid,'nonce':nonce,'intended_exit':0})]:(d/(name+'.json')).write_text(json.dumps(v))
   (d/'marker.raw').write_bytes(a.marker());rows.append({'mode':mode,'folder':mode,'pid':pid,'nonce':nonce,'marker_sha256':a.H(a.marker()),'marker_bytes':1024,'error_name':'AbortError','error_code':'ABORT_ERR','stdout':json.dumps({'owned_child_pid':pid,'nonce':nonce}),'stderr':'','abort_at':1,'settled_at':2 if i==0 else 5,'exit_at':3,'close_at':4,'exit_code':0,'close_code':0,'exit_signal':None,'close_signal':None,'signal_code_at_settlement':None,'marker_present_at_settlement':i==1,'exit_code_at_settlement':None if i==0 else 0,'exit_seen_at_settlement':i==1,'close_seen_at_settlement':i==1})
  self.v={'pid':100,'rows':rows,'native_UI_execution':False,'provider_target_UI_settlement_qualified':False,'product_integration':False}
 def test_positive_and_independent_bytes(self):
  r=a.rows_observed(self.p,self.v);self.assertEqual(r['marker_bytes_compared'],2048);self.assertFalse(r['provider_target_UI_settlement_qualified']);self.assertEqual(a.marker()[:8],bytes([0,31,62,93,13,44,75,106]));self.assertEqual(a.marker()[20:32],b'\xa5'*12)
 def test_rehashed_marker_padding_tail(self):
  q=self.p/'owned-documents/default/marker.raw';original=q.read_bytes()
  for off in [0,20,1023]:
   raw=bytearray(original);raw[off]^=1;q.write_bytes(raw);v=copy.deepcopy(self.v);v['rows'][0]['marker_sha256']=a.H(raw)
   with self.assertRaises(ValueError):a.rows_observed(self.p,v)
  q.write_bytes(original)
 def test_temporal_and_terminal_faults(self):
  for i,k,v in [(0,'settled_at',6),(1,'settled_at',2),(0,'exit_code',False),(1,'exit_code_at_settlement',False),(0,'marker_present_at_settlement',True),(0,'pid',True)]:
   value=copy.deepcopy(self.v);value['rows'][i][k]=v
   with self.assertRaises(ValueError):a.rows_observed(self.p,value)
 def test_identity_scope_and_inventory(self):
  v=copy.deepcopy(self.v);v['provider_target_UI_settlement_qualified']=True
  with self.assertRaises(ValueError):a.rows_observed(self.p,v)
  q=self.p/'owned-documents/default/ready.json';v=json.loads(q.read_text());v['ppid']=999;q.write_text(json.dumps(v))
  with self.assertRaises(ValueError):a.rows_observed(self.p,self.v)
if __name__=='__main__':unittest.main()
