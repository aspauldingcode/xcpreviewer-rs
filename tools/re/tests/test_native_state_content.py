import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_native_state_content import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/native-state-content-2026-10-11'
class NativeStateContentTests(unittest.TestCase):
 def test_seal_reader_fixture(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['owned_state_content_qualified']);self.assertEqual((ROOT/'tools/re/fixtures/StateContentReference.swift').read_bytes(),(E/'StateContentReference.swift').read_bytes())
 def test_resealed_faults(self):
  for fault in ['wait','callback','action','renderer','probe','association','window','pixel','padding','tail','reset-color','scope','helper','missing','prediction']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'run-0/result.json';d=json.loads(p.read_text())
    if fault in ['pixel','padding','tail']:
     p=e/'run-0/initial.raw';b=bytearray(p.read_bytes());b[0 if fault=='pixel' else 68 if fault=='padding' else 16383]^=1;p.write_bytes(b);d=None
    elif fault=='reset-color':p=e/'run-0/changed-id.raw';shutil.copyfile(e/'run-0/changed-immediate.raw',p);d=None
    elif fault=='wait':p=e/'run-0/wait.json';d=json.loads(p.read_text());d['code']=1
    elif fault=='scope':p=e/'assessment.json';d=json.loads(p.read_text());d['native_ui_input_qualified']=True
    elif fault=='helper':p=e/'environment.json';d=json.loads(p.read_text());d['helper_sha256']='0'*64
    elif fault=='prediction':p=e/'prediction.json';d=json.loads(p.read_text());d['expected_colors'][5]='red'
    elif fault=='callback':d['rows'][0]['callbacks']=0
    elif fault=='action':d['actions'][0]['after']=False
    elif fault=='renderer':d['rows'][4]['renderer_identity']='other'
    elif fault=='probe':d['rows'][6]['probe_identity']='other'
    elif fault=='association':d['rows'][8]['last_alternate']=True
    elif fault=='window':d['owned_windows']=1
    else:d['rows'].pop()
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='1ea180c6dab3f56af446eb2952e30a091104979acef2b08d690203d068747c5d'
