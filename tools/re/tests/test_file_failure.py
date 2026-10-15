import hashlib,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
from verify_file_failure import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/file-failure-diagnostic-2026-10-14'
class FileFailureTests(unittest.TestCase):
 def test_sealed_controls(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'7f73ae4818113ec427534df0e5cfcf0f9384360ebd03559bff38178f59a9caeb')
  self.assertEqual(verify(E)['full_frame_bytes'],131072)
  self.assertEqual((E/'after.js').read_bytes(),(ROOT/'tools/re/reloop/source_file_loop.js').read_bytes())

 def test_resealed_faults(self):
  for fault in range(8):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'after/result.json';d=json.loads(p.read_text());c=d['cases'][0]
    if fault==0:c['pollError']='wrong'
    elif fault==1:c['verifyError']='wrong'
    elif fault==2:c['diagnostics']['lastFailure']=None
    elif fault==3:c['events'][3]['error']='wrong'
    elif fault==4:c['finalStatus']['liveWorkers']=1
    elif fault==5:p=e/'before/result.json';d=json.loads(p.read_text());d['cases'][0]['pollError']=None
    else:p=e/'after/opaque-retained.raw';b=bytearray(p.read_bytes());b[52 if fault==6 else 16383]^=1;p.write_bytes(b);d=None
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
