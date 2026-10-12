import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_malformed_control_drain import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/malformed-control-drain-2026-10-12'
class MalformedControlDrainTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['malformed_frame_drained']);self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'after.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/malformed_control_drain_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/malformed_missing_complete_control.js').read_bytes(),(E/'missing-control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['syntax','abort','drain','parent-wait','remaining','emergency','proxy','injected','identity','child-wait','peer','before','missing','scope','outer-wait','helper']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'native-0/result.json';d=json.loads(p.read_text());rec=d['record']
    if fault=='syntax':d['syntaxError']=False
    elif fault=='abort':rec['privateAbortRequested']=False
    elif fault=='drain':rec['report']['drained']=False
    elif fault=='parent-wait':rec['report']['target_code']=-15
    elif fault=='remaining':rec['report']['remaining_observed']=1
    elif fault=='emergency':rec['emergencyClosed']=True
    elif fault=='proxy':p=e/'native-0/anchor-pid.json';d=json.loads(p.read_text());d['proxy_group']+=1
    elif fault in ['injected','identity']:p=e/'native-0/corruption.json';d=json.loads(p.read_text());d['injected']='{}\n' if fault=='injected' else d['injected'];d['original']['rows'][0]['identity'][2]='/wrong/python' if fault=='identity' else d['original']['rows'][0]['identity'][2]
    elif fault=='child-wait':p=e/'native-0/child-wait.json';d=json.loads(p.read_text());d['raw_status']=0
    elif fault=='peer':p=e/'native-0/child.raw';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='before':p=e/'protocol-before/result.json';d=json.loads(p.read_text());d['record']['report']=rec['report']
    elif fault=='missing':p=e/'missing/result.json';d=json.loads(p.read_text());d['record']['emergencyClosed']=False
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['missing_completion_cleanup_qualified']=True
    elif fault=='outer-wait':p=e/'wait-0.json';d=json.loads(p.read_text());d['code']=1
    else:p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='52052dd7195b8c44ad4acd202b9ac1e26b18f4761c7b967848e0092c66a536b6'
