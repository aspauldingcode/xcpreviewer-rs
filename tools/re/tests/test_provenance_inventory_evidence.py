import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_provenance_inventory import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/provenance-inventory-2026-10-14'
class ProvenanceEvidenceTests(unittest.TestCase):
 def test_retained_scope_correction_and_quarantine(self):
  self.assertEqual(verify(E)['files'],159)
  self.assertEqual((E/'provenance_inventory.py').read_bytes(),(ROOT/'tools/re/provenance_inventory.py').read_bytes())
  self.assertEqual(json.loads((E/'inventory-v2.json').read_text()),json.loads((ROOT/'research/canvas-reviews/provenance-inventory.json').read_text()))
 def test_resealed_false_clean_claims_fail(self):
  for fault in range(7):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'inventory-v2.json';d=json.loads(p.read_text())
    if fault==0:d['files'][0]['clean_handoff_eligible']=True
    elif fault==1:d['files'][0]['origin']='original'
    elif fault==2:d['independent_review_complete']=True
    elif fault==3:d['task_accepted']=True
    elif fault==4:d['files'].pop()
    elif fault==5:d['declared_roots'].remove('tools/re/preview_cli.py')
    else:p=e/'assessment.json';d=json.loads(p.read_text());d['native_acquisition']=True
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
