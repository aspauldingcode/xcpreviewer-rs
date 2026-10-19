import unittest,tempfile,json,hashlib,shutil
from pathlib import Path
from admit import admitted
from predictions import provider,readback
BASE=Path('/Users/8amps/xcpreviewer-rs/research/evidence/surface-ack-timeout-2026-10-19')
class Controls(unittest.TestCase):
 def fixture(self,r,candidate='multiply'):
  shutil.copy2(Path(__file__).parent/'probe.c',r/'probe.c');h=hashlib.sha256((r/'probe.c').read_bytes()).hexdigest()
  for phase in ['compile','output-valid','fixture']:
   for suffix in ['record','outer']:shutil.copy2(BASE/(phase+'-'+suffix+'.json'),r/(phase+'-'+suffix+'.json'))
   p=r/(phase+'-record.json');v=json.loads(p.read_text());v['source_sha256']=h;p.write_text(json.dumps(v))
  f=r/'fixture-record.json';v=json.loads(f.read_text());pid=int(v['record']['stderr'].strip().split(':')[1]);out=[];(r/'owned-documents').mkdir()
  for route in range(2):
   a='route%d-provider.raw'%route;b='route%d-readback.raw'%route;pa=provider(route);pb=readback('divide' if route else candidate);(r/'owned-documents'/a).write_bytes(pa);(r/'owned-documents'/b).write_bytes(pb)
   out.append(dict(pid=pid,route=route,provider_file=a,file=b,provider_sha256=hashlib.sha256(pa).hexdigest(),sha256=hashlib.sha256(pb).hexdigest(),provider_bytes=len(pa),width=256,height=3,image_stride=4160 if route else 1088,image_bits_per_component=32 if route else 8,image_bits_per_pixel=128 if route else 32,image_bitmap_info=8449 if route else 1,stride=4160,allocation_bytes=16384,bits_per_component=32,bits_per_pixel=128,bitmap_info=8449,color_space='kCGColorSpaceLinearSRGB'))
  raw=''.join(json.dumps(x)+'\n' for x in out);v['record'].update(stdout=raw,stdoutBytes=len(raw.encode()),stdoutSha256=hashlib.sha256(raw.encode()).hexdigest());f.write_text(json.dumps(v))
 def test_independent_candidates(self):
  for candidate in ['divide','multiply']:
   with tempfile.TemporaryDirectory() as d:r=Path(d);self.fixture(r,candidate);self.assertEqual(admitted(r)['normalization_candidates_supported'],[candidate])
 def test_readback_regions(self):
  for route,offset in [(0,0),(0,4096),(0,16383),(1,0)]:
   with self.subTest(route=route,offset=offset),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r);f=r/'owned-documents'/('route%d-readback.raw'%route);raw=bytearray(f.read_bytes());raw[offset]^=1;f.write_bytes(raw);self.rehash(r,route,raw)
    with self.assertRaises(ValueError):admitted(r)
 def rehash(self,r,route,raw):
  f=r/'fixture-record.json';v=json.loads(f.read_text());rows=[json.loads(x) for x in v['record']['stdout'].splitlines()];rows[route]['sha256']=hashlib.sha256(raw).hexdigest();s=''.join(json.dumps(x)+'\n' for x in rows);v['record'].update(stdout=s,stdoutBytes=len(s.encode()),stdoutSha256=hashlib.sha256(s.encode()).hexdigest());f.write_text(json.dumps(v))
 def test_provider_and_prerequisites(self):
  for fault in ['provider','missing_output','source']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
    r=Path(d);self.fixture(r)
    if fault=='provider':f=r/'owned-documents/route0-provider.raw';x=bytearray(f.read_bytes());x[1024]^=1;f.write_bytes(x)
    if fault=='missing_output':(r/'output-valid-record.json').unlink()
    if fault=='source':(r/'probe.c').write_text('changed')
    with self.assertRaises((ValueError,FileNotFoundError)):admitted(r)
if __name__=='__main__':unittest.main()
