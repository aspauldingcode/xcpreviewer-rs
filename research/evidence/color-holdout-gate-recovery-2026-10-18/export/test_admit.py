import copy,hashlib,json,struct,tempfile,unittest
from pathlib import Path
from admit import admitted,expected,SAMPLES
sha=lambda x:hashlib.sha256(x).hexdigest()
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'owned-documents').mkdir();self.rows=[]
  for mode in range(2):
   for phase,rgb in enumerate(SAMPLES):
    provider,channels=expected(mode,rgb);data=bytearray(b'\xa5'*4096);pixel=struct.pack('<4f',*channels)
    for y in range(9):data[y*288:y*288+272]=pixel*17
    name='mode%d-phase%d-readback.raw'%(mode,phase);pn='mode%d-phase%d-provider.raw'%(mode,phase);(self.root/'owned-documents'/name).write_bytes(data);(self.root/'owned-documents'/pn).write_bytes(provider)
    bits=8 if mode==0 else 16
    self.rows.append(dict(pid=4242,mode=mode,phase=phase,input_linear=rgb,file=name,sha256=sha(data),provider_file=pn,provider_bytes=len(provider),provider_sha256=sha(provider),width=17,height=9,stride=288,bits_per_component=32,bits_per_pixel=128,bitmap_info=8449,alpha_info=1,color_space='kCGColorSpaceLinearSRGB',allocation_bytes=4096,image_width=17,image_height=9,image_stride=17*bits//2,image_bits_per_component=bits,image_bits_per_pixel=bits*4,image_bitmap_info=1 if mode==0 else 4353,image_alpha_info=1,image_color_space='kCGColorSpaceLinearSRGB' if mode==0 else 'kCGColorSpaceExtendedLinearSRGB'))
  self.save()
 def save(self):
  raw=''.join(json.dumps(x)+'\n' for x in self.rows);self.receipt=dict(error=None,binary_sha256='b'*64,record=dict(report=dict(kind='complete',target_code=0,failure=None,drained=True,remaining_observed=0),emergencyClosed=False,privateAbortRequested=False,stdout=raw,stdoutBytes=len(raw),stdoutSha256=sha(raw.encode()),stderr='owned_tree_pid:4242\n'))
  for n in ['fixture','compile']:(self.root/(n+'-record.json')).write_text(json.dumps(self.receipt))
 def test_positive(self):self.assertEqual(admitted(self.root)['full_bytes_compared'],30084)
 def test_metadata_faults(self):
  good=copy.deepcopy(self.rows)
  for key,value in [('pid',True),('mode',True),('phase',1),('stride',272),('provider_bytes',4096),('input_linear',[True,.375,.8125]),('image_stride',128),('image_bitmap_info',4353),('image_alpha_info',3),('image_color_space','kCGColorSpaceSRGB'),('provider_file','missing.raw')]:
   self.rows=copy.deepcopy(good);self.rows[0][key]=value;self.save()
   with self.assertRaises(Exception):admitted(self.root)
 def test_resealed_byte_faults(self):
  good=copy.deepcopy(self.rows)
  for field,hashfield,offset in [('provider_file','provider_sha256',0),('provider_file','provider_sha256',611),('file','sha256',0),('file','sha256',272),('file','sha256',2592),('file','sha256',4095)]:
   row=self.rows[0];p=self.root/'owned-documents'/row[field];before=p.read_bytes();data=bytearray(before);data[offset]^=1;p.write_bytes(data);row[hashfield]=sha(data);self.save()
   with self.assertRaises(Exception):admitted(self.root)
   p.write_bytes(before);self.rows=copy.deepcopy(good)
 def test_failed_completion(self):
  for key,value in [('target_code',1),('target_code',False),('drained',False),('remaining_observed',1)]:
   self.save();self.receipt['record']['report'][key]=value;(self.root/'fixture-record.json').write_text(json.dumps(self.receipt))
   with self.assertRaises(Exception):admitted(self.root)
if __name__=='__main__':unittest.main()
