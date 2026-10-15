import hashlib,json,unittest
from pathlib import Path
from canvas_graph import read
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/canvas-evidence-crosswalk-2026-10-14'
class CrosswalkEvidenceTests(unittest.TestCase):
 def test_sealed_links_and_unanchored_references_stay_unqualified(self):
  m=read(E/'manifest.json');self.assertEqual(set(m['files']),{str(p.relative_to(E)) for p in E.rglob('*') if p.is_file() and p.name!='manifest.json'})
  for name,row in m['files'].items():
   p=E/name;self.assertFalse(p.is_symlink());b=p.read_bytes();self.assertEqual(len(b),row['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256'])
  result=read(E/'crosswalk.json');sources={n['id']:n for n in read(ROOT/'research/loop/canvas-graph.json')['knowledge']['nodes'] if n['type']=='Evidence'}
  self.assertEqual(len(result['documents']),10);self.assertEqual(result['unique_manifests'],11);links=[]
  for doc in result['documents']:
   n=sources[doc['source_node']];self.assertEqual(doc['source_path'],n['provenance']['path']);self.assertEqual(doc['source_sha256'],n['provenance']['sha256']);self.assertEqual(doc['grade'],n['grade']);self.assertEqual(doc['scope'],n['scope']);self.assertEqual(doc['target_version'],n['target_version']);self.assertFalse(doc['semantic_review_complete'])
   text=(ROOT/doc['source_path']).read_text()
   for link in doc['links']:
    self.assertTrue(link['bytes_verified']);self.assertEqual(link['document_mentions_seal'],link['sha256'] in text);self.assertFalse(link['qualified_for_acceptance']);self.assertFalse(link['semantic_review_complete']);links.append(link)
  self.assertEqual(sum(link['document_mentions_seal'] for link in links),9)
  self.assertEqual({link['path'] for link in links if not link['document_mentions_seal']},{'research/evidence/native-state-binding-2026-10-11/manifest.json','research/evidence/surface-partial-right-2026-10-14/manifest.json'})
  self.assertLessEqual(result['charged_read_bytes'],result['limits']['read_bytes']);self.assertFalse(result['independent_semantic_review_complete']);self.assertFalse(result['task_accepted']);self.assertFalse(result['handoff_approved']);self.assertFalse(result['native_execution'])
  self.assertEqual((E/'canvas_evidence_crosswalk.py').read_bytes(),(ROOT/'tools/re/canvas_evidence_crosswalk.py').read_bytes())
