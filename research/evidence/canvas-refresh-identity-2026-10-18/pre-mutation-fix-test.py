import tempfile,unittest
from pathlib import Path
from PIL import Image
from decode import decode,COLORS,BLACK
class TelemetryTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name)/'frame.png';self.image=Image.new('RGBA',(512,96),BLACK)
  self.pid=4242;self.token=0x123456789abcdef0123456789abcdef0
  rows=[[(i//4)%2==0 for i in range(128)],[(self.pid>>(31-i%32))&1 for i in range(128)],[(self.token>>(127-i))&1 for i in range(128)]];rows.append([not b for b in rows[2]])
  for row,bits in enumerate(rows):
   for col,bit in enumerate(bits):
    if bit:
     for y in range(row*24,(row+1)*24):
      for x in range(col*4,(col+1)*4):self.image.putpixel((x,y),COLORS[row])
  self.image.save(self.p)
 def test_positive(self):
  v=decode(self.p);self.assertEqual(v['pid'],4242);self.assertEqual(v['state_token_hex'],'123456789abcdef0123456789abcdef0');self.assertEqual(v['rgba_bytes_checked'],196608)
 def test_blank_and_geometry(self):
  for size in [(512,96),(511,96),(512,95)]:
   Image.new('RGBA',size,BLACK).save(self.p)
   with self.assertRaises(Exception):decode(self.p)
 def test_interior_palette_alpha_and_redundancy(self):
  for xy,color in [((511,95),(1,2,3,255)),((3,23),(255,0,255,254)),((128,24),(255,0,0,255)),((0,72),COLORS[3])]:
   value=self.image.copy();value.putpixel(xy,color);value.save(self.p)
   with self.subTest(xy=xy),self.assertRaises(Exception):decode(self.p)
if __name__=='__main__':unittest.main()
