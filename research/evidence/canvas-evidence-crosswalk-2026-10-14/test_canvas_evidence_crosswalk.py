import hashlib,json,tempfile,unittest
from pathlib import Path
from canvas_graph import sha
from canvas_evidence_crosswalk import crosswalk
class CanvasEvidenceCrosswalkTests(unittest.TestCase):
 def fixture(self,root,style):
  e=root/'research/evidence/owned';e.mkdir(parents=True);(e/'payload.raw').write_bytes(bytes([0,1,255,165]))
  (e/'manifest.json').write_text(json.dumps({'files':{'payload.raw':{'bytes':4,'sha256':sha(e/'payload.raw')}}}))
  text={'inline':'Evidence: `research/evidence/owned`; manifest `'+sha(e/'manifest.json')+'`.','hash':'Manifest `'+sha(e/'manifest.json')+'`.','path':'[evidence](../../research/evidence/owned/manifest.json)'}[style]
  (root/'report.md').write_text(text)
  return {'knowledge':{'nodes':[{'id':'e:owned','type':'Evidence','grade':'owned-oracle','scope':'owned only','target_version':'fixture','provenance':{'path':'report.md','sha256':sha(root/'report.md')}}]}}
 def test_inline_hash_and_path_resolution_no_acceptance(self):
  for style in ['inline','hash','path']:
   with self.subTest(style=style),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);graph=self.fixture(root,style);r=crosswalk(root,graph);link=r['documents'][0]['links'][0];self.assertTrue(link['bytes_verified']);self.assertFalse(link['qualified_for_acceptance']);self.assertEqual(link['document_mentions_seal'],style!='path');self.assertFalse(r['task_accepted'])
 def test_bad_seal_and_extra_file_quarantined(self):
  for fault in ['payload','extra','symlink']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);graph=self.fixture(root,'inline');e=root/'research/evidence/owned'
    if fault=='payload':(e/'payload.raw').write_bytes(b'bad')
    elif fault=='extra':(e/'unsealed').write_text('owned')
    else:(e/'payload.raw').unlink();(e/'payload.raw').symlink_to(root/'report.md')
    self.assertFalse(crosswalk(root,graph)['documents'][0]['links'][0]['bytes_verified'])
 def test_changed_document_and_budget_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);graph=self.fixture(root,'inline')
   with self.assertRaises(ValueError):crosswalk(root,graph,max_bytes=1)
   (root/'report.md').write_text('changed')
   with self.assertRaises(ValueError):crosswalk(root,graph)
