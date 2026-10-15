import json,subprocess,tempfile,unittest
from pathlib import Path
from provenance_inventory import inventory,snapshot,MAX_FILE

class ProvenanceInventoryTests(unittest.TestCase):
 def test_tracked_untracked_asset_and_exposure_no_clean_claim(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);subprocess.run(['git','init','-q',str(root)],check=True)
   (root/'src').mkdir();(root/'src/a.rs').write_text('owned fixture');(root/'src/icon.svg').write_text('<svg/>')
   subprocess.run(['git','-C',str(root),'add','src/a.rs'],check=True)
   subprocess.run(['git','-C',str(root),'-c','user.name=Owned','-c','user.email=owned@example.invalid','commit','-qm','owned fixture'],check=True)
   (root/'src/a.rs').write_text('changed owned fixture')
   result=inventory(root,['src']);self.assertEqual(result['counts']['files'],2);self.assertEqual(result['counts']['assets'],1)
   self.assertEqual(result['files'][0]['tracking'],'tracked');self.assertEqual(result['files'][1]['tracking'],'untracked')
   self.assertFalse(result['task_accepted']);self.assertFalse(result['independent_review_complete']);self.assertTrue(all(not x['clean_handoff_eligible'] for x in result['files']))
 def test_symlink_and_oversize_rejected_without_reading(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);target=root/'real';target.write_text('owned');link=root/'link';link.symlink_to(target)
   with self.assertRaises(OSError):snapshot(link)
   large=root/'large';large.write_bytes(b'X'*(MAX_FILE+1))
   with self.assertRaisesRegex(ValueError,'size limit'):snapshot(large)
