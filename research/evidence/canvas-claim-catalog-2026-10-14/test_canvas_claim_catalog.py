import copy,tempfile,unittest
from pathlib import Path
from canvas_graph import ROOT,read,sha
from canvas_claim_catalog import catalog,verify_catalog
class CanvasClaimCatalogTests(unittest.TestCase):
 def test_actual_pilot_is_50_candidates_not_50_reviewed_claims(self):
  result=catalog(ROOT,read(ROOT/'research/loop/canvas-graph.json'));self.assertEqual(result['statement_candidates'],50);self.assertEqual(result['pilot_documents'],10);self.assertEqual(verify_catalog(ROOT,result)['literal_spans_verified'],50)
  self.assertFalse(result['quality_gate']['passed']);self.assertIsNone(result['quality_gate']['precision'])
 def test_tampering_and_automatic_acceptance_fail(self):
  result=catalog(ROOT,read(ROOT/'research/loop/canvas-graph.json'))
  for fault in ['quote','span','line','id','acceptance','precision','review','grade']:
   with self.subTest(fault=fault):
    d=copy.deepcopy(result);r=d['records'][0]
    if fault=='quote':r['quote']='fabricated statement'
    elif fault=='span':r['char_span'][0]+=1
    elif fault=='line':r['line_span'][0]+=1
    elif fault=='id':r['id']='0'*64
    elif fault=='acceptance':r['qualified_for_acceptance']=True
    elif fault=='precision':d['quality_gate']['precision']=1
    elif fault=='review':r['semantic_review']='accepted'
    else:r['source_grade']='native-correlated'
    with self.assertRaises(AssertionError):verify_catalog(ROOT,d)
 def test_source_identity_and_bounds_rejected(self):
  graph=read(ROOT/'research/loop/canvas-graph.json');graph['knowledge']['nodes'][0]['provenance']['sha256']='0'*64
  with self.assertRaises(ValueError):catalog(ROOT,graph)
  with self.assertRaises(ValueError):catalog(ROOT,graph,100)
