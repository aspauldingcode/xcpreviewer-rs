import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from verify_native_raw_output import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/native-raw-output-2026-10-12'
class NativeRawOutputTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['controlled_peer_bytes'],32);self.assertEqual((ROOT/'tools/re/tests/native_raw_output_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'observed_compiler.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['count','digest','text-digest','text','empty-digest','combined','manual','error','abort','receipt','emergency','parent-wait','child-wait','peer','hash','write','order','identity','outer-wait','helper','runtime','slots']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'invalid-exact/result.json';d=json.loads(p.read_text());rec=d['record']
    if fault=='count':rec['stderrBytes']=196608
    elif fault=='digest':rec['stderrSha256']='0'*64
    elif fault=='text-digest':rec['stderrSha256']=hashlib.sha256(rec['stderr'].encode()).hexdigest()
    elif fault=='text':rec['stderr']='x'
    elif fault=='empty-digest':rec['stdoutSha256']='0'*64
    elif fault=='combined':rec['stdoutBytes']=1
    elif fault=='manual':d['manualAbort']=False
    elif fault=='error':d['error']='Error: Observed compiler output limit'
    elif fault=='abort':rec['privateAbortRequested']=False
    elif fault=='receipt':rec['report']=None
    elif fault=='emergency':rec['emergencyClosed']=True
    elif fault=='parent-wait':rec['report']['target_code']=0
    elif fault=='child-wait':p=e/'invalid-exact/child-wait.json';d=json.loads(p.read_text());d['raw_status']=0
    elif fault=='peer':p=e/'invalid-exact/child.raw';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault in ['hash','identity']:p=e/'invalid-exact/injection.json';d=json.loads(p.read_text());d['plan'][0]['sha256']='0'*64 if fault=='hash' else d['plan'][0]['sha256'];d['original']['rows'][0]['identity'][2]='/wrong/python' if fault=='identity' else d['original']['rows'][0]['identity'][2]
    elif fault=='write':p=e/'invalid-exact/injection-write.json';d=json.loads(p.read_text());d[0]['written_bytes']=0
    elif fault=='order':p=e/'mixed-invalid/injection-write.json';d=json.loads(p.read_text());d.reverse()
    elif fault=='outer-wait':p=e/'wait-invalid-exact.json';d=json.loads(p.read_text());d['code']=1
    elif fault=='helper':p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['sha256']='0'*64
    elif fault=='runtime':p=e/'environment.json';d=json.loads(p.read_text());d['runtime_sha256']='0'*64
    else:p=e/'slots.json';d=json.loads(p.read_text());d['used']=5
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='12c9af3842f2b5cddd491553ee4ed4214918c8a75c2cbb879f3aa6177f70c5ab'
