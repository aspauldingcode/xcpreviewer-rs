import unittest,json,copy
from pathlib import Path
from path_binding import assess,validate_binding
b=json.loads((Path(__file__).parent/'path-binding.json').read_text())
def ax(project=False,reverse=False):
 url='file://'+b['project' if project else 'source']['observed'];desc=b['project']['observed']
 root=f'URL: {url}, ID: Xcode.WorkspaceWindow' if not reverse else f'ID: Xcode.WorkspaceWindow, URL: {url}'
 tab=f'Description: {desc}, ID: Workspace window tab content' if not reverse else f'ID: Workspace window tab content, Description: {desc}'
 return f'0 standard window PreviewLab, {root}, Secondary Actions: Raise\n\t1 split group PreviewLab.xcodeproj, {tab}\n\t\t2 text entry area Description: Source Editor\n\t3 close button\n'
class Tests(unittest.TestCase):
 def test_attribute_orders(self):
  for reverse in [False,True]:self.assertEqual(assess(ax(reverse=reverse),b),{'close_index':3,'source_context':True})
 def test_project_context_separate(self):
  with self.assertRaises(ValueError):assess(ax(project=True),b)
  self.assertFalse(assess(ax(project=True),b,False)['source_context'])
 def test_wrong_source(self):
  with self.assertRaises(ValueError):assess(ax().replace('/Sources/PreviewLab/PreviewLab.swift','/Sources/PreviewLab/Other.swift'),b)
 def test_wrong_project(self):
  with self.assertRaises(ValueError):assess(ax().replace('Description: /tmp/','Description: /elsewhere/'),b)
 def test_remote_query_fragment(self):
  for old,new in [('file:///tmp/','file://remote/tmp/'),('PreviewLab.swift,','PreviewLab.swift?x=1,'),('PreviewLab.swift,','PreviewLab.swift#x,')]:
   with self.assertRaises(ValueError):assess(ax().replace(old,new),b)
 def test_duplicate_attribute_index_window(self):
  for text in [ax().replace('URL: file:', 'URL: file:///bad, URL: file:'),ax()+'\t3 close button\n',ax()+'4 standard window Extra, ID: Xcode.WorkspaceWindow\n']:
   with self.assertRaises(ValueError):assess(text,b)
 def test_alias_not_generalized(self):
  v=copy.deepcopy(b);v['source']['observed']='/var/other.swift'
  with self.assertRaises(ValueError):validate_binding(v)
 def test_inode_mismatch(self):
  v=copy.deepcopy(b);v['source']['observed_stat'][1]+=1
  with self.assertRaises(ValueError):validate_binding(v)
 def test_boolean_float_stat(self):
  for z in [True,1.0]:
   v=copy.deepcopy(b);v['source']['observed_stat'][0]=z
   with self.assertRaises(ValueError):validate_binding(v)
 def test_encoded_separator_wrong_context(self):
  with self.assertRaises(ValueError):assess(ax().replace('PreviewLab.swift','PreviewLab.swift%2Fother'),b)
 def test_unrelated_root_ancestry(self):
  for anchor in ['\t1 split group','\t3 close button']:
   with self.assertRaises(ValueError):assess(ax().replace(anchor,'7 container unrelated\n'+anchor),b)
 def test_malformed_depth(self):
  for text in [ax().replace('\t1 split group','\t\t1 split group'),ax().replace('\t3 close button','\t\t\t3 close button')]:
   with self.assertRaises(ValueError):assess(text,b)
if __name__=='__main__':unittest.main()
