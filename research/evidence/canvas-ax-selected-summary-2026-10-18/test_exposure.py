import unittest,json
from pathlib import Path
from exposure import scan
b=json.loads((Path(__file__).parent/'path-binding.json').read_text());project=b['project']['observed'];source=b['source']['observed']
base=f'0 standard window PreviewLab, URL: file://{source}, ID: Xcode.WorkspaceWindow\n\t1 split group PreviewLab.xcodeproj, Description: {project}, ID: Workspace window tab content\n'
end='\t9 close button\n'
class Tests(unittest.TestCase):
 def test_finite_named_nodes(self):
  a=base+'\t\t2 container ID: owned.callback.root\n\t\t\t3 text Count: 0, ID: owned.callback.count\n\t\t\t4 button Owned Increment, ID: owned.callback.increment\n'+end
  v=scan(a,b);self.assertTrue(v['unique_all_identifiers_observed']);self.assertFalse(v['native_action_authorized'])
 def test_source_editor_excluded(self):
  a=base+'\t\t2 text entry area Description: Source Editor\n\t\t\t3 button Owned Increment, ID: owned.callback.increment\n'+end
  self.assertFalse(scan(a,b)['matches']['owned.callback.increment'])
 def test_literal_text_not_identifier(self):
  a=base+'\t\t2 text owned.callback.increment\n'+end
  self.assertFalse(scan(a,b)['matches']['owned.callback.increment'])
 def test_duplicate_not_unique(self):
  a=base+'\t\t2 container ID: owned.callback.root\n\t\t\t3 text Count: 0, ID: owned.callback.count\n\t\t\t4 button Owned Increment, ID: owned.callback.increment\n\t\t\t5 button Owned Increment, ID: owned.callback.increment\n'+end
  self.assertFalse(scan(a,b)['unique_all_identifiers_observed'])
 def test_wrong_ancestry_reject(self):
  with self.assertRaises(ValueError):scan(base.replace('\t1 split','7 container unrelated\n\t1 split')+end,b)
 def test_wrong_source_reject(self):
  with self.assertRaises(ValueError):scan(base.replace(source,source+'.other')+end,b)
if __name__=='__main__':unittest.main()
