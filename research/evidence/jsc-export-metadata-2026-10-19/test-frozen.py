import unittest,importlib.util,tempfile,shutil,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen',root/'verify-frozen.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Tests(unittest.TestCase):
 def test_positive(self):self.assertTrue(v.observations(root)['both_failures_retained'])
 def test_failure_rejects_promotions(self):
  for label,key,value in [('first-rejection','target_code',0),('changed-rejection','target_code',True),('metadata-only','remaining_observed',1)]:
   with self.subTest(label=label,key=key),tempfile.TemporaryDirectory() as t:
    p=Path(t)/'e';shutil.copytree(root,p,ignore=shutil.ignore_patterns('__pycache__'));q=p/label/'fixture-record.json';r=json.loads(q.read_text());r['record']['report'][key]=value;q.write_text(json.dumps(r))
    with self.assertRaises(ValueError):v.observations(p)
 def test_rehashed_metadata(self):
  for key,value in [('scalar_dispatches',1),('module_valid',False),('exports',[{'name':'multiplyBits','kind':'function'}]),('non_Apple_OS_verified',True)]:
   with self.subTest(key=key),tempfile.TemporaryDirectory() as t:
    p=Path(t)/'e';shutil.copytree(root,p,ignore=shutil.ignore_patterns('__pycache__'));q=p/'metadata-only'/'fixture-record.json';r=json.loads(q.read_text());out=json.loads(r['record']['stdout']);out[key]=value;s=json.dumps(out)+'\n';r['record'].update(stdout=s,stdoutBytes=len(s.encode()),stdoutSha256=hashlib.sha256(s.encode()).hexdigest());q.write_text(json.dumps(r))
    with self.assertRaises(ValueError):v.observations(p)
 def test_source_and_buffer(self):
  for fault in ['source','buffer']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as t:
    p=Path(t)/'e';shutil.copytree(root,p,ignore=shutil.ignore_patterns('__pycache__'));q=p/'metadata-only'
    if fault=='source':(q/'probe.js').write_text((q/'probe.js').read_text()+'\n// changed\n')
    else:(q/'owned-documents'/'invented.raw').write_bytes(b'\0')
    with self.assertRaises(ValueError):v.observations(p)
if __name__=='__main__':unittest.main()
