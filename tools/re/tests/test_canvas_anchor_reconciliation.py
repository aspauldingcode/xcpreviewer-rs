import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_canvas_anchors import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/canvas-anchor-reconciliation-2026-10-14'
class CanvasAnchorReconciliationTests(unittest.TestCase):
 def test_frozen_manifest_bytes_match_repository_objects(self):
  self.assertEqual(verify(E)['repository_anchors'],2)
 def test_resealed_trust_and_object_faults_rejected(self):
  for fault in range(7):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'anchors.json';d=json.loads(p.read_text());r=d['rows'][0]
    if fault==0:r['document_mentions_seal']=True
    elif fault==1:r['independent_external_trust']=True
    elif fault==2:r['qualified_for_acceptance']=True
    elif fault==3:r['git_blob']='0'*40
    elif fault==4:r['commit']='0'*40
    elif fault==5:d['task_accepted']=True
    else:p=e/r['frozen_manifest'];p.write_bytes(p.read_bytes()+b' ');d=None
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
