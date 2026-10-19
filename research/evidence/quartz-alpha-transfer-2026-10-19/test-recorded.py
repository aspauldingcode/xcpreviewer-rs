import unittest,tempfile,shutil,json,hashlib
from pathlib import Path
from admit import observed,admit
p=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_numerical_rejection_is_retained(self):
  with self.assertRaises(ValueError):admit(p)
  r=observed(p);self.assertFalse(r['primary_alpha_invariant_exact']);self.assertTrue(r['opaque_gray_conversion_operational_range']);self.assertFalse(r['opaque_gray_bit_exact_model_qualified']);self.assertEqual(r['comparisons'][1]['comparisons'][0]['mismatch_bytes'],0)
 def test_rehashed_provider_padding_tail(self):
  for provider,offset in [(True,3072),(False,12288),(False,49151)]:
   with self.subTest(provider=provider,offset=offset),tempfile.TemporaryDirectory() as t:
    e=Path(t)/'e';shutil.copytree(p,e,ignore=shutil.ignore_patterns('probe','__pycache__'));q=e/'fixture-record.json';v=json.loads(q.read_text());rows=[json.loads(s) for s in v['record']['stdout'].splitlines()];name='route0-provider.raw' if provider else 'route0-readback.raw';f=e/'owned-documents'/name;b=bytearray(f.read_bytes());b[offset]^=1;f.write_bytes(b);rows[0]['provider_sha256' if provider else 'sha256']=hashlib.sha256(b).hexdigest();s=''.join(json.dumps(r)+'\n' for r in rows);v['record'].update(stdout=s,stdoutBytes=len(s.encode()),stdoutSha256=hashlib.sha256(s.encode()).hexdigest());q.write_text(json.dumps(v))
    with self.assertRaises(ValueError):observed(e)
 def test_typed_terminal_rejection(self):
  for field in ['target_code','remaining_observed']:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as t:
    e=Path(t)/'e';shutil.copytree(p,e,ignore=shutil.ignore_patterns('probe','__pycache__'));q=e/'fixture-record.json';v=json.loads(q.read_text());v['record']['report'][field]=False;q.write_text(json.dumps(v))
    with self.assertRaises(ValueError):observed(e)
if __name__=='__main__':unittest.main()
