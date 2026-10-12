import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from verify_native_failure_wait import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/native-failure-wait-2026-10-12'
class NativeFailureWaitTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['controlled_peer_bytes'],32);self.assertEqual((ROOT/'tools/re/tests/native_failure_wait_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'observed_compiler.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['error','success-error','abort','receipt','emergency','root-wait','failure-reason','tracked','child-wait','peer','empty-digest','intent','release','identity','finish','outer-wait','helper','runtime','slots']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'failure-0/result.json';d=json.loads(p.read_text());rec=d['record']
    if fault=='error':d['error']=None
    elif fault=='success-error':p=e/'success-0/result.json';d=json.loads(p.read_text());d['error']='Error: failure'
    elif fault=='abort':rec['privateAbortRequested']=True
    elif fault=='receipt':rec['report']=None
    elif fault=='emergency':rec['emergencyClosed']=True
    elif fault=='root-wait':rec['report']['target_code']=0
    elif fault=='failure-reason':rec['report']['failure']='abort'
    elif fault=='tracked':rec['report']['tracked']=1
    elif fault=='child-wait':p=e/'failure-0/child-wait.json';d=json.loads(p.read_text());d['raw_status']=0
    elif fault=='peer':p=e/'failure-0/child.raw';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b);d=None
    elif fault=='empty-digest':rec['stdoutSha256']='0'*64
    elif fault=='intent':p=e/'failure-0/exit-intent.json';d=json.loads(p.read_text());d['after_child_wait']=False
    elif fault=='release':d['released']=False
    elif fault=='identity':p=e/'failure-0/release-observation.json';d=json.loads(p.read_text());d[0]['identity'][2]='/wrong/python'
    elif fault=='finish':p=e/'failure-0/finish';p.write_text('wrong');d=None
    elif fault=='outer-wait':p=e/'wait-failure-0.json';d=json.loads(p.read_text());d['code']=1
    elif fault=='helper':p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    elif fault=='runtime':p=e/'environment.json';d=json.loads(p.read_text());d['runtime_sha256']='0'*64
    else:p=e/'slots.json';d=json.loads(p.read_text());d['used']=5
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='d6d7bbe09f9d4f1d926764224808affd11433025dffc4a96f9d60d3b8bd9989e'
