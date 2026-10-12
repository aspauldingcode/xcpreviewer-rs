import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_superseded_build_cancel import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/superseded-build-cancel-2026-10-11'
class SupersededBuildCancelTests(unittest.TestCase):
 def test_seal_sources_and_reader(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['cooperative_supersession_cancel_verified']);self.assertEqual((ROOT/'tools/re/reloop/source_file_loop.js').read_bytes(),(E/'source-file-loop-after.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/superseded_build_cancel_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['abort','manual','old','generation','cleanup','padding','tail','prediction','native','budget','missing','error']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e)
    if fault in ['padding','tail','prediction']:
     p=e/'after-valid/final.raw';b=bytearray(p.read_bytes());b[52 if fault=='padding' else 448]^=1;p.write_bytes(b);d=None
     if fault=='prediction':(e/'expectations/2.raw').write_bytes(b)
    elif fault=='native':p=e/'scope.json';d=json.loads(p.read_text());d['native_canvas_qualified']=True
    elif fault=='budget':p=e/'environment.json';d=json.loads(p.read_text());d['budgets']['node_seconds']=30
    else:
     p=e/'results.json';d=json.loads(p.read_text());r=next(x for x in d if x['phase']=='after' and x['mode']=='valid')
     if fault=='abort':r['aborts']=0
     elif fault=='manual':r['manuallyReleased']=True
     elif fault=='old':d[0]['cancelledBeforeManualRelease']=True
     elif fault=='generation':next(x for x in r['events'] if x['kind']=='published' and x['generation']==3)['generation']=2
     elif fault=='cleanup':r['finalStatus']['liveWorkers']=1
     elif fault=='error':next(x for x in r['events'] if x['kind']=='rejected')['error']='No cancellation proof'
     else:d.pop()
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='4065b1cf591e9468a66482d48d9739a87f262085775f33fc1ce85a12dd24b601'
