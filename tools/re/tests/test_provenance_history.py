import subprocess,tempfile,unittest
from pathlib import Path
from provenance_history import audit
class ProvenanceHistoryTests(unittest.TestCase):
 def test_repository_order_does_not_grant_clean_status(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   def git(*args):return subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True,text=True,timeout=10).stdout
   git('init','-q');git('config','user.name','Owned');git('config','user.email','owned@example.invalid')
   (root/'analysis.md').write_text('owned research fixture');git('add','analysis.md');git('commit','-qm','research');first=git('rev-parse','HEAD').strip()
   (root/'candidate.rs').write_text('owned fixture');git('add','candidate.rs');git('commit','-qm','candidate')
   report=audit(root,['candidate.rs'],['analysis.md']);row=report['candidates'][0];self.assertEqual(row['comparisons'][0]['analysis_addition'],first);self.assertTrue(row['comparisons'][0]['analysis_is_ancestor']);self.assertFalse(row['clean_handoff_eligible']);self.assertFalse(report['task_accepted'])
 def test_scope_escape_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):audit(Path(tmp),['../escape'],['anchor'])
