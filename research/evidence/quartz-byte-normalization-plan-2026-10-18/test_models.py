import struct,unittest
from fractions import Fraction
from models import f32_bits,from_bits,predict,domain
class ExactTests(unittest.TestCase):
    def test_full_byte_domain_independent_double_crosscheck(self):
        for k in range(256):
            self.assertEqual(predict(k,'division'),struct.pack('<f',k/255))
            reciprocal=struct.unpack('<f',struct.pack('<f',1/255))[0]
            self.assertEqual(predict(k,'reciprocal'),struct.pack('<f',k*reciprocal))
    def test_halfway_even_and_significand_carry(self):
        for bits in [0x3a800000,0x3b808081,0x3efffffe,0x3effffff,0x3f000000,0x3f7ffffe,0x3f7fffff]:
            self.assertEqual(f32_bits(from_bits(bits)),bits)
            midpoint=(from_bits(bits)+from_bits(bits+1))/2
            self.assertEqual(f32_bits(midpoint),bits if bits%2==0 else bits+1)
    def test_invalid_domain(self):
        for x in [True,-1,256,1.0]:
            with self.assertRaises(ValueError):predict(x,'division')
        with self.assertRaises(ValueError):predict(1,'unknown')
        for x in [-1,3,Fraction(1,2**127)]:
            with self.assertRaises(ValueError):f32_bits(x)
    def test_model_separator(self):
        rows=domain();self.assertEqual(len(rows),256)
        self.assertEqual(sum(r['division_hex']!=r['reciprocal_hex'] for r in rows),126)
        for k in [0,255]:self.assertEqual(predict(k,'division'),predict(k,'reciprocal'))
if __name__=='__main__':unittest.main()
