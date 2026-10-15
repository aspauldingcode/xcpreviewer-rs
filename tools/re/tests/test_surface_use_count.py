import hashlib,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
from verify_surface_use_count import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/surface-use-count-2026-10-14'
class SurfaceUseCountTests(unittest.TestCase):
 def test_sealed_controls(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'7be8c766a3947b76cb91e9a0b537dfc00a97f71722e5284799f05846fe400723')
  self.assertEqual(verify(E)['full_allocation_bytes'],98304)
  self.assertEqual((E/'probe.m').read_bytes(),(ROOT/'tools/re/surface_use_count.m').read_bytes())

 def test_resealed_faults(self):
  for fault in range(8):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'0/result.json';d=json.loads(p.read_text())
    if fault==0:d['states'][0]['original_in_use']=False
    elif fault==1:d['states'][2]['alias_count']=1
    elif fault==2:d['alias_only_in_use']=True
    elif fault==3:d['final_ref_status']=0
    elif fault==4:d['same_id']=False
    elif fault==5:p=e/'0-wait.json';d=json.loads(p.read_text());d['code']=1
    else:p=e/'0/alias-only.raw';b=bytearray(p.read_bytes());b[68 if fault==6 else 16383]^=1;p.write_bytes(b);d=None
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
