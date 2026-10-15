import hashlib,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
from verify_thenable_callback import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/thenable-callback-2026-10-14'

class ThenableCallbackTests(unittest.TestCase):
 def test_source_and_native_controls(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'d7ea916d9d6d23b371cf5425f0b76665b09fb70c6aeb6a555368442f4b31ac3b')
  self.assertTrue(verify(E)['thenable_results_rejected'])
  self.assertEqual((E/'after.js').read_bytes(),(ROOT/'tools/re/reloop/observed_compiler.js').read_bytes())

 def test_resealed_faults(self):
  for fault in range(12):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'after-results.json';d=json.loads(p.read_text())
    if fault==0:p=e/'before-results.json';d=json.loads(p.read_text());d[1]['unhandled']=[]
    elif fault==1:d[0]['error']=None
    elif fault==2:d[1]['error']['message']='wrong'
    elif fault==3:d[2]['record']['privateAbortRequested']=False
    elif fault==4:d[3]['thenCalls']=0
    elif fault==5:d[4]['error']['message']='wrong'
    elif fault==6:d[5]['error']={'name':'Error','message':'wrong'}
    elif fault in [7,8,9]:
     p=e/'native-rejected/result.json';d=json.loads(p.read_text())
     if fault==7:d['syncContractRejected']=False
     elif fault==8:d['record']['report']['drained']=False
     else:d['record']['report']['target_code']=0
    elif fault==10:p=e/'native-rejected/child-wait.json';d=json.loads(p.read_text());d['raw_status']=0
    else:p=e/'native-rejected/child.raw';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
