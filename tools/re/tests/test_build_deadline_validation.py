import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_build_deadline_validation import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/build-deadline-validation-2026-10-12'
class BuildDeadlineValidationTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['invalid_deadline_no_new_root_verified']);self.assertEqual(hashlib.sha256((E/'after.js').read_bytes()).hexdigest(),'edf649aa54604d1f30550f568adf22cfe9da3f88651797bb8cb43fb0ae291349');self.assertEqual((ROOT/'tools/re/tests/build_deadline_validation_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['root','before','existing','files','error','value','valid','budget','handoff','sentinel','scope','wait','prediction']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text())
    if fault=='root':d['rows'][17]['rootExists']=True
    elif fault=='before':d['rows'][0]['rootExists']=False
    elif fault=='existing':d['rows'][18]['existing']=False
    elif fault=='files':d['rows'][18]['files']=[]
    elif fault=='error':d['rows'][17]['error']='Unexpected failure'
    elif fault=='value':d['rows'][27]['value']=1
    elif fault=='valid':d['rows'][31]['valid']=False
    elif fault=='budget':d['rows'][31]['budget']['stagesCreated']=1
    elif fault=='handoff':d['syntheticHandoffs']=1
    elif fault=='sentinel':p=e/'after/invalid-18/sentinel';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['per_stage_byte_quota_qualified']=True
    elif fault=='wait':p=e/'environment.json';d=json.loads(p.read_text());d['wait_code']=1
    else:p=e/'prediction.json';d=json.loads(p.read_text());d['after_invalid_new_root_created']=True
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='bcb1e161eb299470d3cd5d7ee1d52ceda29da2c9754dc942fc0f8c19c77c0e95'
