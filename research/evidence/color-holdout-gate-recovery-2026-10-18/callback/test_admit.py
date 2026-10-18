import copy,hashlib,json,struct,tempfile,unittest
from pathlib import Path
from admit import admitted,predicted,SAMPLES
sha=lambda data:hashlib.sha256(data).hexdigest()
class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'owned-documents').mkdir();self.rows=[]
  for mode in range(2):
   for phase,rgb in enumerate(SAMPLES):
    bits,values=predicted(rgb)
    for route in range(3):
     data=bytearray(b'\xa5'*4096);pixel=struct.pack('<4f',*rgb,1)
     for y in range(9):data[y*288:y*288+272]=pixel*17
     name='mode%d-phase%d-route%d.raw'%(mode,phase,route);(self.root/'owned-documents'/name).write_bytes(data)
     self.rows.append(dict(pid=4242,mode=mode,phase=phase,route=route,file=name,sha256=sha(data),input_linear=rgb,encoded_half_bits=bits,encoded_half_components=values,callbacks=int(route==2),reported_size=[17,9],width=17,height=9,stride=288,bits_per_component=32,bits_per_pixel=128,bitmap_info=8449,alpha_info=1,color_space='kCGColorSpaceLinearSRGB',allocation_bytes=4096))
  self.save()
 def save(self):
  raw=''.join(json.dumps(x)+'\n' for x in self.rows)
  report=dict(kind='complete',target_code=0,failure=None,drained=True,remaining_observed=0)
  record=dict(report=report,emergencyClosed=False,privateAbortRequested=False,stdout=raw,stdoutBytes=len(raw),stdoutSha256=sha(raw.encode()),stderr='owned_tree_pid:4242\n')
  self.receipt=dict(error=None,binary_sha256='a'*64,record=record)
  (self.root/'fixture-record.json').write_text(json.dumps(self.receipt));(self.root/'compile-record.json').write_text(json.dumps(self.receipt))
 def rewrite(self):
  (self.root/'fixture-record.json').write_text(json.dumps(self.receipt))
 def test_positive(self):self.assertTrue(admitted(self.root)['half_source_sufficient_for_holdouts'])
 def test_valid_nonmatching_countermodel(self):
  for row in self.rows:
   if row['route']==2:
    p=self.root/'owned-documents'/row['file'];data=bytearray(p.read_bytes());rgb=[.125,.5,.75] if row['phase']!=1 else [.25,.75,.875];pixel=struct.pack('<4f',*rgb,1)
    for y in range(9):data[y*288:y*288+272]=pixel*17
    p.write_bytes(data);row['sha256']=sha(data)
  self.save();self.assertFalse(admitted(self.root)['half_source_sufficient_for_holdouts'])
 def test_resealed_metadata_faults(self):
  good=copy.deepcopy(self.rows)
  cases=[('pid',True),('mode',True),('phase',1),('route',2),('width',18),('stride',272),('bits_per_component',16),('bitmap_info',1),('alpha_info',3),('allocation_bytes',4095),('input_linear',[True,.375,.8125]),('encoded_half_components',[True,0,0]),('encoded_half_bits',[True,1,1]),('callbacks',True),('reported_size',[True,9]),('color_space','wrong'),('file','missing.raw')]
  for key,value in cases:
   with self.subTest(key=key):
    self.rows=copy.deepcopy(good);self.rows[0][key]=value;self.save()
    with self.assertRaises(Exception):admitted(self.root)
 def test_bytes_and_receipts(self):
  good=copy.deepcopy(self.rows)
  for offset in [0,12,272,2592,4095]:
   p=self.root/'owned-documents'/self.rows[0]['file'];before=p.read_bytes();data=bytearray(before);data[offset]^=1;p.write_bytes(data);self.rows[0]['sha256']=sha(data);self.save()
   with self.assertRaises(Exception):admitted(self.root)
   p.write_bytes(before);self.rows=copy.deepcopy(good)
  self.save()
  for key,value in [('target_code',1),('target_code',False),('drained',False),('remaining_observed',1)]:
   self.save();self.receipt['record']['report'][key]=value;self.rewrite()
   with self.assertRaises(Exception):admitted(self.root)
  self.save();self.receipt['record']['stdoutSha256']='0'*64;self.rewrite()
  with self.assertRaises(Exception):admitted(self.root)
if __name__=='__main__':unittest.main()
