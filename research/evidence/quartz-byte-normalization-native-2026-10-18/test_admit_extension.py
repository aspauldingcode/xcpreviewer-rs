"""Post-measurement synthetic coverage; approved native sources/pins unchanged."""
import hashlib,json,struct,unittest
import test_admit as base
from admit import admitted
class SemanticControls(unittest.TestCase):
 setUp=base.Controls.setUp
 write_fixture=base.Controls.write_fixture
 def rebind(self,blocks):
  f=json.loads((self.r/'fixture-record.json').read_text());rows=[json.loads(x) for x in f['record']['stdout'].splitlines()]
  for phase,data in enumerate(blocks):
   (self.r/'owned-documents'/('phase%d.raw'%phase)).write_bytes(data);rows[phase]['sha256']=hashlib.sha256(data).hexdigest()
  self.write_fixture(rows)
 def test_neither_model_positive(self):
  data=bytearray((self.r/'prospective-reciprocal.raw').read_bytes())
  for y in range(3):
   for x in range(256):data[y*4112+x*16:y*4112+x*16+16]=struct.pack('<4f',0.25,0.25,0.25,1)
  self.rebind([data,data]);v=admitted(self.r)
  self.assertTrue(v['measurement_receipts_admitted'])
  self.assertTrue(all(all(n>0 for n in row['model_mismatch_bytes'].values()) for row in v['results']))
 def test_hash_rebound_semantic_faults(self):
  original=(self.r/'prospective-reciprocal.raw').read_bytes()
  for offset,replacement in [(4096,b'\x00'),(12336,b'\x00'),(16383,b'\x00'),(12,struct.pack('<f',0.5)),(0,struct.pack('<f',float('nan')))]:
   data=bytearray(original);data[offset:offset+len(replacement)]=replacement;self.rebind([data,data])
   with self.subTest(offset=offset),self.assertRaises(Exception):admitted(self.r)
 def test_hash_rebound_repeat_fault(self):
  original=(self.r/'prospective-reciprocal.raw').read_bytes();changed=bytearray(original);changed[:4]=struct.pack('<f',0.5)
  self.rebind([original,changed])
  with self.assertRaises(Exception):admitted(self.r)
 def test_linked_output_and_source(self):
  for name in ['source.raw','phase0.raw']:
   p=self.r/'owned-documents'/name;data=p.read_bytes();p.unlink();other=self.r/'linked-target';other.write_bytes(data);p.symlink_to(other)
   with self.subTest(name=name),self.assertRaises(Exception):admitted(self.r)
   p.unlink();other.unlink();p.write_bytes(data)
if __name__=='__main__':unittest.main()
