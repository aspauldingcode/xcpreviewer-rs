import unittest,copy
from profile import summarize
class Tests(unittest.TestCase):
 def rows(self):return [{'event':'verify_start','run_id':'a','declared_files':2,'declared_bytes':8},{'event':'verify_finish','run_id':'a','valid':True,'external_anchor_matches':True,'seconds':0.1},{'event':'graph_result','all_milestones_complete':False}]
 def test_valid_and_duplicate_calls_counted(self):
  r=self.rows();v=summarize(r[:2]+r);self.assertEqual((v['verification_calls'],v['unique_runs'],v['declared_files_across_calls'],v['declared_bytes_across_calls']),(2,1,4,16))
 def test_missing_finish(self):
  with self.assertRaises(ValueError):summarize(self.rows()[::2])
 def test_wrong_run_binding(self):
  r=self.rows();r[1]['run_id']='b'
  with self.assertRaises(ValueError):summarize(r)
 def test_rejected_or_unanchored(self):
  for key in ['valid','external_anchor_matches']:
   r=self.rows();r[1][key]=False
   with self.assertRaises(ValueError):summarize(r)
 def test_counts_and_acceptance_not_coerced(self):
  for key,value in [('declared_files',True),('declared_bytes',-1)]:
   r=self.rows();r[0][key]=value
   with self.assertRaises(ValueError):summarize(r)
  r=self.rows();r[-1]['all_milestones_complete']=True
  with self.assertRaises(ValueError):summarize(r)
 def test_incomplete_and_extra_result(self):
  r=self.rows()
  for bad in [r[:-1],r+[r[-1]],r+[r[0]],r+[{'event':'invented'}]]:
   with self.assertRaises(ValueError):summarize(bad)
if __name__=='__main__':unittest.main()
