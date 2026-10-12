import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from verify_raw_output_accounting import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/raw-output-accounting-2026-10-12'
class RawOutputTests(unittest.TestCase):
 def test_seal_sources_reader(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['injected_controls'],48);self.assertEqual((ROOT/'tools/re/reloop/observed_compiler.js').read_bytes(),(E/'after.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/raw_output_accounting_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['raw','count','stderr-count','digest','stderr-digest','text-digest','text','phase','abort','later-count','report','chunk','claim','wait']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'results.json';d=json.loads(p.read_text());x=d[28];rec=x['record']
    if fault=='raw':p=e/'invalid-exact-0.raw';b=bytearray(p.read_bytes());b[0]=0;p.write_bytes(b);d=None
    elif fault=='count':rec['stdoutBytes']=196608
    elif fault=='stderr-count':d[32]['record']['stderrBytes']=196608
    elif fault=='digest':rec['stdoutSha256']='0'*64
    elif fault=='stderr-digest':d[32]['record']['stderrSha256']='0'*64
    elif fault=='text-digest':rec['stdoutSha256']=hashlib.sha256(rec['stdout'].encode()).hexdigest()
    elif fault=='text':rec['stdout']='x'
    elif fault=='phase':d[4]['record']['stdoutBytes']=65536
    elif fault=='abort':d[25]['record']['privateAbortRequested']=False
    elif fault=='later-count':d[34]['record']['stderrBytes']=0
    elif fault=='report':rec['report']['tracked']=1
    elif fault=='chunk':d[30]['chunks']=[{'fd':1,'bytes':4}]
    elif fault=='claim':p=e/'prediction.json';d=json.loads(p.read_text());d['native_cleanup_qualified']=True
    else:p=e/'wait.json';d=json.loads(p.read_text());d['code']=1
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='a9457eb6c3b639dae37905e819eef891658c1c2bdaf2415cd0480226ad506314'
