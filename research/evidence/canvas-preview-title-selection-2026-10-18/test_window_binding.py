import unittest
from window_binding import bind
class Tests(unittest.TestCase):
 def fixture(self):
  project='/private/tmp/owned/PreviewLab.xcodeproj';source='/private/tmp/owned/Sources/PreviewLab/PreviewLab.swift'
  ax='0 standard window PreviewLab, ID: Xcode.WorkspaceWindow, Secondary Actions: Raise, URL: file://'+source+'\n\t1 split group PreviewLab.xcodeproj, ID: Workspace window tab content, Description: '+project+'\n\t93 close button\n'
  windows={'structuredContent':{'message':'* tabIdentifier: t1, workspacePath: '+project+'\n'}}
  return ax,windows,project,source
 def test_exact(self):self.assertEqual(bind(*self.fixture())['close_index'],93)
 def test_sibling_prefix(self):
  a,w,p,s=self.fixture();w['structuredContent']['message']+='* tabIdentifier: t2, workspacePath: '+p+'-other\n';self.assertEqual(bind(a,w,p,s)['tab'],'t1')
  with self.assertRaises(ValueError):bind(a,w,p+'-other',s)
 def test_source_url(self):
  a,w,p,s=self.fixture()
  for bad in [a.replace('file:///','file://remote/'),a.replace('.swift','.swift?x'),a.replace('.swift','.swift#x'),a.replace('URL: file://'+s,'URL: file://'+s+'-other')]:
   with self.assertRaises(ValueError):bind(bad,w,p,s)
 def test_duplicate_root_and_close(self):
  a,w,p,s=self.fixture()
  for bad in [a+a,a+'\t94 close button\n',a.replace('\t93 close button\n','')]:
   with self.assertRaises(ValueError):bind(bad,w,p,s)
 def test_wrong_project_description(self):
  a,w,p,s=self.fixture()
  with self.assertRaises(ValueError):bind(a.replace('Description: '+p,'Description: '+p+'-other'),w,p,s)
 def test_error_and_ambiguous_broker(self):
  a,w,p,s=self.fixture();w['isError']=True
  with self.assertRaises(ValueError):bind(a,w,p,s)
  del w['isError'];w['structuredContent']['message']*=2
  with self.assertRaises(ValueError):bind(a,w,p,s)
if __name__=='__main__':unittest.main()
