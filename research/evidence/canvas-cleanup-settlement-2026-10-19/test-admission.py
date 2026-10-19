import unittest,tempfile,shutil,json
from pathlib import Path
from admit import admit
P=Path(__file__).resolve().parent
class Admission(unittest.TestCase):
 def test_positive(self):self.assertEqual(admit(P)['model_cases'],25)
 def test_corrupted_model_records(self):
  for fault in ['case_false','native_claim','prototype_success','variant_missing','source_hash','syntax_failure','boolean_exit']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
    p=Path(d)/'p';shutil.copytree(P,p,ignore=shutil.ignore_patterns('__pycache__'));v=json.loads((p/'controls.json').read_text());r=v['records'][0]
    if fault in ['case_false','native_claim']:
     o=json.loads(r['stdout'])
     if fault=='case_false':o['cases'][0]['passed']=False
     else:o['native_eligible']=True
     r['stdout']=json.dumps(o)
    if fault=='prototype_success':v['records'][1]['exit']=0
    if fault=='variant_missing':v['records'].pop()
    if fault=='source_hash':r['source_sha256']='0'*64
    if fault=='syntax_failure':v['records'][1]['syntax_exit']=1
    if fault=='boolean_exit':r['exit']=False
    (p/'controls.json').write_text(json.dumps(v))
    with self.assertRaises(ValueError):admit(p)
if __name__=='__main__':unittest.main()
