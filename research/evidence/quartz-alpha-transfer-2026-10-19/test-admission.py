import unittest,tempfile,json,hashlib,copy
from pathlib import Path
from predictions import provider,readback
from admit import rows_observed
H=lambda b:hashlib.sha256(b).hexdigest()
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name);(self.p/'owned-documents').mkdir();self.rows=[]
  for i in range(3):
   a='route%d-provider.raw'%i;b='route%d-readback.raw'%i;src=provider(i);dst=readback(i,'iec_srgb' if i==2 else 'alpha_invariant');(self.p/'owned-documents'/a).write_bytes(src);(self.p/'owned-documents'/b).write_bytes(dst)
   self.rows.append(dict(pid=123,route=i,provider_bytes=9408,width=768,height=3,image_stride=3136,image_bits_per_component=8,image_bits_per_pixel=32,image_bitmap_info=1,stride=12352,allocation_bytes=49152,bits_per_component=32,bits_per_pixel=128,bitmap_info=8449,color_space='kCGColorSpaceLinearSRGB',source_color_space='kCGColorSpaceLinearSRGB' if i==1 else 'kCGColorSpaceSRGB',provider_file=a,file=b,provider_sha256=H(src),sha256=H(dst)))
 def tearDown(self):self.t.cleanup()
 def test_positive(self):
  r=rows_observed(self.p,self.rows);self.assertTrue(r['primary_alpha_invariant_exact']);self.assertTrue(r['opaque_gray_conversion_operational_range']);self.assertEqual(r['all_bytes_compared'],175680)
 def test_rehashed_padding_tail(self):
  q=self.p/'owned-documents'/'route0-readback.raw';raw=q.read_bytes()
  for off in [12288,37056,49151]:
   with self.subTest(off=off):
    b=bytearray(raw);b[off]^=1;q.write_bytes(b);rows=copy.deepcopy(self.rows);rows[0]['sha256']=H(b)
    with self.assertRaises(ValueError):rows_observed(self.p,rows)
    q.write_bytes(raw)
 def test_unsupported_models_remain_diagnostic(self):
  q=self.p/'owned-documents'/'route0-readback.raw';b=readback(0,'transfer_premultiplied');q.write_bytes(b);self.rows[0]['sha256']=H(b);r=rows_observed(self.p,self.rows);self.assertFalse(r['primary_alpha_invariant_exact']);self.assertFalse(r['transfer_on_premultiplied_candidate_rejected'])
 def test_provider_and_metadata(self):
  for key,value in [('width',True),('source_color_space','wrong'),('image_bitmap_info',0)]:
   with self.subTest(key=key):
    rows=copy.deepcopy(self.rows);rows[0][key]=value
    with self.assertRaises(ValueError):rows_observed(self.p,rows)
  q=self.p/'owned-documents'/'route0-provider.raw';b=bytearray(q.read_bytes());b[3072]^=1;q.write_bytes(b);self.rows[0]['provider_sha256']=H(b)
  with self.assertRaises(ValueError):rows_observed(self.p,self.rows)
if __name__=='__main__':unittest.main()
