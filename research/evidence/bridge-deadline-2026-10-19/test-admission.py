from pathlib import Path
import unittest,tempfile,shutil,json
from admit import admit
P=Path(__file__).resolve().parent
class Admission(unittest.TestCase):
 def test_positive(self):self.assertEqual(admit(P)['marker_bytes_compared'],18)
 def test_corrupt_receipts(self):
  for fault in ['order','float_clock','no_join','socket_not_removed','marker_byte','source_hash','boolean_exit','upstream_claim','fake_status_success']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'p';shutil.copytree(P,p,ignore=shutil.ignore_patterns('__pycache__'));o=json.loads((p/'execution.json').read_text());v=json.loads(o['stdout']);a,b=v['records']
    if fault=='order':b['journal'][1],b['journal'][3]=b['journal'][3],b['journal'][1]
    if fault=='float_clock':b['journal'][0]['at_ns']=float(b['journal'][0]['at_ns'])
    if fault=='no_join':b['server_joined']=False
    if fault=='socket_not_removed':a['socket_cleanup_verified']=False
    if fault=='marker_byte':b['late_effect_hex']=b'owned-late-effect!'.hex()
    if fault=='source_hash':v['source_sha256']='0'*64
    if fault=='boolean_exit':o['exit']=False
    if fault=='upstream_claim':v['upstream_Apple_request']=True
    if fault=='fake_status_success':a['actual_status_response_verified']=True
    o['stdout']=json.dumps(v);(p/'execution.json').write_text(json.dumps(o))
    with self.assertRaises(ValueError):admit(p)
if __name__=='__main__':unittest.main()
