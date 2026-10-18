import json,tempfile,unittest
from pathlib import Path
from bindings import owned_tab,payload
class BindingTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name)/'PreviewLab.xcodeproj';self.p.mkdir()
 def response(self,path=None):return {'structuredContent':{'message':'* tabIdentifier: windowtab1, workspacePath: %s\n'%(path or self.p)}}
 def test_exact_and_canonical_binding(self):
  self.assertEqual(owned_tab(self.response(),self.p),'windowtab1')
  self.assertEqual(owned_tab(self.response(str(self.p.parent/'subdir/../PreviewLab.xcodeproj')),self.p),'windowtab1')
 def test_suffix_prefix_relative_and_other_rejected(self):
  for path in [str(self.p)+'.backup','prefix'+str(self.p),'PreviewLab.xcodeproj',str(self.p.parent/'Other.xcodeproj')]:
   with self.subTest(path=path),self.assertRaises(ValueError):owned_tab(self.response(path),self.p)
 def test_duplicates_and_missing_rejected(self):
  for message in ['', 'No workspace windows found',self.response()['structuredContent']['message']*2]:
   with self.subTest(message=message),self.assertRaises(ValueError):owned_tab({'structuredContent':{'message':message}},self.p)
 def test_tool_failure_dominates_populated_success_fields(self):
  for code in [True,1,None,'false']:
   value=self.response();value['isError']=code;value['structuredContent']['previewSnapshotPath']='/tmp/not-success.png'
   with self.subTest(code=code),self.assertRaises(ValueError):payload(value)
 def test_success_and_text_fallback(self):
  value=self.response();value['isError']=False;self.assertEqual(owned_tab(value,self.p),'windowtab1')
  value={'content':[{'type':'text','text':json.dumps(value['structuredContent'])}]};self.assertEqual(owned_tab(value,self.p),'windowtab1')
 def test_invalid_objects(self):
  for value in [None,[],{'content':[]},{'structuredContent':[]},{'content':[{'type':'image'}]}]:
   with self.subTest(value=value),self.assertRaises(Exception):payload(value)
if __name__=='__main__':unittest.main()
