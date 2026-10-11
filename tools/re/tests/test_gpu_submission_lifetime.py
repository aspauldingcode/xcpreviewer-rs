import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('submission_reader',Path(__file__).with_name('verify_gpu_submission_lifetime.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SubmissionLifetimeTests(unittest.TestCase):
 def test_native_submission_and_destruction_callbacks(self):
  e=ROOT/'research/evidence/gpu-submission-lifetime-2026-10-11';self.assertEqual((ROOT/'tools/re/gpu_submission_lifetime.m').read_bytes(),(e/'gpu_submission_lifetime.m').read_bytes());self.assertEqual(reader.verify(e)['complete_bytes'],196608)
 def test_resealed_false_completion_timeout_owner_and_padding(self):
  for kind in ['wait','status','timeout','owner','callback','padding']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/gpu-submission-lifetime-2026-10-11',e);p=e/'result-0.json';d=json.loads(p.read_text());row=d['rows'][1]
    if kind=='wait':(e/'wait-0.json').write_text(json.dumps({'code':1,'timeout':False,'stderr':''}))
    elif kind=='status':d['rows'][0]['completion_status']=4
    elif kind=='timeout':row['bounded_wait_timed_out']=False
    elif kind=='owner':row['weak_buffer_after_construction_pool']=False
    elif kind=='callback':row['callbacks_before_release']=1
    else:
     b=bytearray(base64.b64decode(row['after']));b[44]^=1;row['after']=base64.b64encode(b).decode()
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
