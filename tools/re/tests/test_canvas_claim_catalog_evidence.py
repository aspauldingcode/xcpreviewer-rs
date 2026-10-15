import hashlib,json,unittest
from pathlib import Path
from canvas_claim_catalog import verify_catalog
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/canvas-claim-catalog-2026-10-14'
class CanvasClaimCatalogEvidenceTests(unittest.TestCase):
 def test_sealed_catalog_and_review_boundary(self):
  m=json.loads((E/'manifest.json').read_text());self.assertEqual(set(m['files']),{str(p.relative_to(E)) for p in E.rglob('*') if p.is_file() and p.name!='manifest.json'})
  for name,row in m['files'].items():
   p=E/name;self.assertFalse(p.is_symlink());b=p.read_bytes();self.assertEqual(len(b),row['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256'])
  result=json.loads((E/'catalog.json').read_text());self.assertEqual(verify_catalog(ROOT,result)['literal_spans_verified'],50)
  self.assertEqual(result,json.loads((ROOT/'research/canvas-reviews/evidence-coverage-audit.json').read_text()))
  self.assertEqual((E/'canvas_claim_catalog.py').read_bytes(),(ROOT/'tools/re/canvas_claim_catalog.py').read_bytes())
  assessment=json.loads((E/'assessment.json').read_text());self.assertFalse(assessment['independent_semantic_review_complete']);self.assertFalse(assessment['knowledge_fusion_performed']);self.assertFalse(assessment['task_accepted'])
