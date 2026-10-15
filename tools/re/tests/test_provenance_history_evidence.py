import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_provenance_history import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/provenance-history-2026-10-14'
class ProvenanceHistoryEvidenceTests(unittest.TestCase):
 def test_ancestry_is_not_clean_authorship(self):
  self.assertEqual(verify(E)['ancestry_checks'],12)
  self.assertEqual((E/'provenance_history.py').read_bytes(),(ROOT/'tools/re/provenance_history.py').read_bytes())
 def test_resealed_false_provenance_claims(self):
  for fault in range(7):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'history.json';d=json.loads(p.read_text())
    if fault==0:d['candidates'][0]['clean_handoff_eligible']=True
    elif fault==1:d['candidates'][0]['origin']='original'
    elif fault==2:d['candidates'][0]['comparisons'][0]['analysis_is_ancestor']=False
    elif fault==3:d['task_accepted']=True
    elif fault==4:d['candidates'].pop()
    else:
     p=e/'independent-ancestry.json';d=json.loads(p.read_text())
     if fault==5:d[0]['commits']=[]
     else:d[0]['code']=1
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
