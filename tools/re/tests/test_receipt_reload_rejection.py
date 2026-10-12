import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_receipt_reload_rejection import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/receipt-reload-rejection-2026-10-12'
class ReceiptReloadRejectionTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['last_valid_frame_retained']);self.assertEqual((ROOT/'tools/re/tests/receipt_reload_rejection_control.js').read_bytes(),(E/'control.js').read_bytes())
  for name in ['rust_source_builder.js','source_file_loop.js','rust_receipt.js','bounded_artifact.js','source_revision_host.js','live_wasm_host.js']:self.assertEqual((ROOT/'tools/re/reloop'/name).read_bytes(),(E/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['worker','busy','generation','published','oracle','handoff','budget','failure','report','stdout','baseline','pixel','padding','tail','scope','wait']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'result.json';d=json.loads(p.read_text());row=d['rows'][0]
    if fault=='worker':row['finalStatus']['liveWorkers']=1
    elif fault=='busy':row['failureSnapshot']['busy']=True
    elif fault=='generation':row['events'][3]['generation']=3
    elif fault=='published':row['events'][3]['kind']='published'
    elif fault=='oracle':row['oracleCalls']=3
    elif fault=='handoff':row['handoffs']=2
    elif fault=='budget':row['budget']['stagesCreated']=2
    elif fault=='failure':row['failures']=[]
    elif fault=='report':row['failures'][0]['record']['report']['drained']=False
    elif fault=='stdout':row['failures'][0]['record']['stdout']='{}'
    elif fault=='baseline':p=e/'receipt-json/retained.raw';shutil.copyfile(e/'receipt-json/recovered.raw',p);d=None
    elif fault in ['pixel','padding','tail']:p=e/'receipt-json/retained.raw';b=bytearray(p.read_bytes());b[0 if fault=='pixel' else 52 if fault=='padding' else 16383]^=1;p.write_bytes(b);d=None
    elif fault=='scope':p=e/'scope.json';d=json.loads(p.read_text());d['native_canvas_qualified']=True
    else:p=e/'environment.json';d=json.loads(p.read_text());d['wait_code']=1
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='787422a6b8c83946b9e0652be0506cd130265651a1aa321a07fd7257acae0e45'
