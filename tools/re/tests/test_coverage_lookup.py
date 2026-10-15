import tempfile,unittest
from pathlib import Path
from coverage_lookup import lookup
class CoverageLookupTests(unittest.TestCase):
 def test_prior_anchor_is_discovery_not_acceptance(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);docs=root/'docs/reverse-engineering';docs.mkdir(parents=True);e=root/'research/evidence/old';e.mkdir(parents=True);(e/'manifest.json').write_text('{}')
   (docs/'old.md').write_text('# Alias use-count\n[sealed](../../research/evidence/old/manifest.json)')
   result=lookup(root,['alias','use count']);self.assertEqual(result['decision'],'review-existing-evidence');self.assertFalse(result['delivery_accepted']);self.assertEqual(len(result['matches'][0]['anchors']),1)
   self.assertEqual(lookup(root,['unseen'])['decision'],'no-text-match')
 def test_external_anchor_and_symlink_ignored(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);docs=root/'docs/reverse-engineering';docs.mkdir(parents=True)
   (docs/'a.md').write_text('# Alias\n[bad](/private/tmp/manifest.json)')
   (docs/'b.md').symlink_to(docs/'a.md')
   result=lookup(root,['alias']);self.assertEqual(len(result['matches']),1);self.assertEqual(result['matches'][0]['anchors'],[])
