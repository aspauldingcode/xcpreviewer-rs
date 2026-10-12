import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_abort_close_reentry import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/abort-close-reentry-2026-10-11'
class AbortCloseReentryTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['reentrant_close_respected']);self.assertEqual((ROOT/'tools/re/reloop/source_file_loop.js').read_bytes(),(E/'source-file-loop-after.js').read_bytes());self.assertEqual((ROOT/'tools/re/tests/abort_close_reentry_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  for fault in ['before','after','aborts','calls','frame','worker','generation','padding','tail','oracle','native','budget','missing']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e)
    if fault in ['padding','tail','oracle']:
     p=e/'after-valid/baseline.raw';b=bytearray(p.read_bytes());b[52 if fault=='padding' else 448]^=1;p.write_bytes(b);d=None
     if fault=='oracle':(e/'expected.raw').write_bytes(b)
    elif fault=='native':p=e/'scope.json';d=json.loads(p.read_text());d['native_canvas_qualified']=True
    elif fault=='budget':p=e/'environment.json';d=json.loads(p.read_text());d['budgets']['node_seconds']=30
    else:
     p=e/'results.json';d=json.loads(p.read_text());r=next(x for x in d if x['phase']=='after' and x['mode']=='valid')
     if fault=='before':d[0]['observedError']=None
     elif fault=='after':r['observedError']='Source host closed'
     elif fault=='aborts':r['aborts']=2
     elif fault=='calls':r['buildCalls']=3
     elif fault=='frame':r['frameCleared']=False
     elif fault=='worker':r['finalStatus']['liveWorkers']=1
     elif fault=='generation':next(x for x in r['events'] if x['kind']=='observed')['generation']=3
     else:d.pop()
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='27e16b965b987dabd0d982fde26239e13eaac5dcd81f6590306f4c74fe8ca626'
