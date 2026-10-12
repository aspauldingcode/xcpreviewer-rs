import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_mixed_output_cancel import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/mixed-output-cancel-2026-10-12'
class MixedOutputCancelTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['combined_limit'],65536);self.assertEqual((ROOT/'tools/re/tests/mixed_output_cancel_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'observed_compiler.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['manual','error','abort','receipt','emergency','parent-wait','child-wait','peer','hash','write','order','quota','prefix','exact','combined','identity','outer-wait','helper']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'mixed-stdout-first/result.json';d=json.loads(p.read_text());rec=d['record']
    if fault=='manual':d['manualAbort']=True
    elif fault=='error':d['error']='Error: Observed compiler aborted'
    elif fault=='abort':rec['privateAbortRequested']=False
    elif fault=='receipt':rec['report']=None
    elif fault=='emergency':rec['emergencyClosed']=True
    elif fault=='parent-wait':rec['report']['target_code']=0
    elif fault=='child-wait':p=e/'mixed-stdout-first/child-wait.json';d=json.loads(p.read_text());d['raw_status']=0
    elif fault=='peer':p=e/'mixed-stdout-first/child.raw';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault in ['hash','identity']:p=e/'mixed-stdout-first/injection.json';d=json.loads(p.read_text());d['plan'][0]['sha256']='0'*64 if fault=='hash' else d['plan'][0]['sha256'];d['original']['rows'][0]['identity'][2]='/wrong/python' if fault=='identity' else d['original']['rows'][0]['identity'][2]
    elif fault in ['write','order']:p=e/'mixed-stdout-first/injection-write.json';d=json.loads(p.read_text());d[0]['written_bytes']=0 if fault=='write' else d[0]['written_bytes'];d.reverse() if fault=='order' else None
    elif fault=='quota':p=e/'scope.json';d=json.loads(p.read_text());d['per_stream_quota_claim']=True
    elif fault=='prefix':rec['stderr']='z'
    elif fault=='exact':p=e/'stderr-exact/result.json';d=json.loads(p.read_text());d['record']['stderr']='y'*65535
    elif fault=='combined':rec['stdout']='x'*32768;rec['stderr']='y'*32769
    elif fault=='outer-wait':p=e/'wait-mixed-stdout-first.json';d=json.loads(p.read_text());d['code']=1
    else:p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='a834e8daa1bfdb0211f6460ca095318c9cd3a7a0233f1cf64dddb37026e22125'
