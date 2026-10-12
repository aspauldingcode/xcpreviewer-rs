import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_actual_builder_cancel import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/actual-builder-cancel-2026-10-11'
class ActualBuilderCancelTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['actual_owned_builder_cancel_qualified'])
  for name in ['source_file_loop.js','observed_group_anchor.py']:self.assertEqual((ROOT/'tools/re/reloop'/name).read_bytes(),(E/name).read_bytes())
  self.assertEqual(hashlib.sha256((E/'observed_compiler.js').read_bytes()).hexdigest(),'0e117bcddafceb46ee735b15d2468722f1e2161f17799ed2d1aa21c4a3b87e09')
  self.assertEqual(hashlib.sha256((E/'rust_source_builder.js').read_bytes()).hexdigest(),'d3e32ce1faf68ea6ca382ace3c5962a9398eb6adc2606fe537c20c098222193a')
  self.assertEqual((ROOT/'tools/re/tests/actual_builder_cancel_control.js').read_bytes(),(E/'control.js').read_bytes())
 def test_resealed_faults(self):
  faults=['qualified','trigger','birth','generation','wait','cleanup','abort','signal','success','padding','tail','partial','module','scope','worker','helper','cache','oracle']
  for fault in faults:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());fail=d['failures'][0]['record']
    if fault in ['padding','tail','oracle']:
     p=e/'baseline.raw';b=bytearray(p.read_bytes());b[52 if fault=='padding' else 448]^=1;p.write_bytes(b);d=None
     if fault=='oracle':(e/'retained-at-cancel.raw').write_bytes(b);(e/'0-expected.raw').write_bytes(b)
    elif fault=='partial':p=e/'builds'/d['trigger']['stage']/'result/view.wasm';p.write_bytes(b'partial');d=None
    elif fault=='module':p=e/'builds'/d['records'][0]['stage']/'result/view.wasm';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['arbitrary_process_quiescence_qualified']=True
    elif fault=='helper':p=e/'environment.json';d=json.loads(p.read_text());d['observer_sha256']='0'*64
    elif fault=='qualified':d['qualified']=False
    elif fault=='trigger':d['trigger']['moduleAbsentBeforeCancel']=False
    elif fault=='birth':d['trigger']['compiler']['identity'][0]+=1
    elif fault=='generation':d['events'][-1]['generation']=2
    elif fault=='wait':fail['report']['target_code']=0
    elif fault=='cleanup':fail['report']['drained']=False
    elif fault=='abort':fail['report']['failure']='deadline'
    elif fault=='signal':fail['signal']='SIGTERM'
    elif fault=='success':d['records'][0]['execution']['report']['target_code']=2
    elif fault=='worker':d['finalStatus']['liveWorkers']=1
    else:d['records'][0]['receipt']['cache_hit']=True
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='634fff5175a8cfd4041085e09caf7d1d7607e0f6a3a38b2d4d3963698a08abeb'
