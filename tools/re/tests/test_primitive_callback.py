import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_primitive_callback import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/primitive-callback-2026-10-14'

class PrimitiveCallbackTests(unittest.TestCase):
 def test_source_and_native_controls(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'cc30d90cbf294b92d37b9ab76e5d31b4bb899d038eeb2f71ace5a4e0e044d71f')
  self.assertTrue(verify(E)['primitive_failure_preserved'])
  self.assertEqual((E/'after.js').read_bytes(),(ROOT/'tools/re/reloop/observed_compiler.js').read_bytes())

 def test_resealed_faults(self):
  for fault in ['reason','immutable','identity','opaque','before','abort','kill','native','drain','root-wait','child-wait','payload']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'after-results.json';d=json.loads(p.read_text())
    if fault=='reason':d[1]['error']['message']='Observed compiler failed: abort'
    elif fault=='immutable':d[10]['error']['originalIdentity']=True
    elif fault=='identity':d[9]['error']['originalIdentity']=False
    elif fault=='opaque':d[8]['error']['name']='TypeError'
    elif fault=='before':p=e/'before-results.json';d=json.loads(p.read_text());d[0]['settled']=True
    elif fault=='abort':d[0]['record']['privateAbortRequested']=False
    elif fault=='kill':d[0]['kills']=[]
    elif fault in ['native','drain','root-wait']:
     p=e/'native-false/result.json';d=json.loads(p.read_text())
     if fault=='native':d['normalizedOriginal']=False
     elif fault=='drain':d['record']['report']['drained']=False
     else:d['record']['report']['target_code']=0
    elif fault=='child-wait':p=e/'native-false/child-wait.json';d=json.loads(p.read_text());d['raw_status']=0
    else:p=e/'native-false/child.raw';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
