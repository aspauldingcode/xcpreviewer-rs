import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from verify_unicode_output_accounting import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/unicode-output-accounting-2026-10-12'
class UnicodeOutputTests(unittest.TestCase):
 def test_seal_sources_reader(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(verify(E)['injected_controls'],16);self.assertEqual((ROOT/'tools/re/tests/unicode_output_accounting_control.js').read_bytes(),(E/'control.js').read_bytes());self.assertEqual(hashlib.sha256((E/'production.js').read_bytes()).hexdigest(),'dc164e0c7feb85554d2c485f58363d17dce9f6ae1f57c206f1501db532ee2a56')
 def test_resealed_faults(self):
  for fault in ['raw','hash','text','text-bytes','raw-bytes','abort','error','chunk','report','kill','native-claim','wait']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'results.json';d=json.loads(p.read_text());x=d[4]
    if fault=='raw':p=e/'invalid-exact.raw';b=bytearray(p.read_bytes());b[0]=0;p.write_bytes(b);d=None
    elif fault=='hash':x['input_sha256']='0'*64
    elif fault=='text':x['record']['stdout']='x'
    elif fault=='text-bytes':x['text_utf8_bytes']=65536
    elif fault=='raw-bytes':x['retained_raw_bytes']=196608
    elif fault=='abort':d[1]['record']['privateAbortRequested']=False
    elif fault=='error':d[1]['error']=None
    elif fault=='chunk':d[6]['chunks']=[4]
    elif fault=='report':x['record']['report']['tracked']=1
    elif fault=='kill':x['killCalls']=[]
    elif fault=='native-claim':p=e/'prediction.json';d=json.loads(p.read_text());d['native_cleanup_qualified']=True
    else:p=e/'wait.json';d=json.loads(p.read_text());d['code']=1
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='1be39dfaa5a82f4d988b47ee1f59a09eb24f6478d8ba7e9ad4daa65663bd92ce'
