import tempfile
import unittest
from pathlib import Path
from reloop.portablealpha import expected, CAPACITY
from reloop.verification import bytes_equal


class PortableAlphaTests(unittest.TestCase):
    def test_native_holdout_values_padding_and_tail(self):
        for n,pixel in [(1,(32,0,223,255)),(4,(128,0,127,255)),(6,(191,0,64,255))]:
            raw=expected(17,9,80,n,1)
            self.assertEqual(raw[:4],bytes(pixel))
            self.assertEqual(raw[68:80],b'\xcd'*12)
            self.assertEqual(raw[720:],b'\xa5'*(CAPACITY-720))
        self.assertEqual(expected(1,1,4,0,0)[:4],b'\x00'*4)
        self.assertEqual(len(expected(64,64,256,8,0)),CAPACITY)

    def test_invalid_geometry_and_modes_reject(self):
        for args in [(0,9,80,4,1),(65,9,80,4,1),(17,65,80,4,1),(17,9,67,4,1),
                     (17,9,257,4,1),(17,9,80,9,1),(17,9,80,4,2),(True,9,80,4,1),
                     (17,9,80,-1,1),(17,9,80,4,1.0)]:
            with self.assertRaises(ValueError):expected(*args)

    def test_full_allocation_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'expected';b=Path(tmp)/'actual';raw=expected(17,9,80,4,1);a.write_bytes(raw)
            for offset in (0,3,68,719,720,CAPACITY-1):
                changed=bytearray(raw);changed[offset]^=1;b.write_bytes(changed)
                comparison=bytes_equal(a,b)
                self.assertFalse(comparison['passed']);self.assertEqual(comparison['different_bytes'],1)
            b.write_bytes(raw[:-1]);self.assertFalse(bytes_equal(a,b)['passed'])
