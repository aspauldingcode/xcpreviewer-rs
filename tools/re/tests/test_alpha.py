import tempfile
import unittest
from pathlib import Path
from reloop.alpha import expected
from reloop.verification import bytes_equal


class AlphaPredictionTests(unittest.TestCase):
    def test_complement_and_holdouts(self):
        self.assertEqual(expected(5)[:4], bytes((128, 0, 127, 255)))
        self.assertEqual(expected(6)[:4], bytes((32, 0, 223, 255)))
        self.assertEqual(expected(7)[:4], bytes((191, 0, 64, 255)))
        for variant in range(8):
            self.assertEqual(len(expected(variant)), 612)
        for variant in (-1, 8, True, 1.0):
            with self.assertRaises(ValueError):
                expected(variant)

    def test_all_pixel_channels_and_tails_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp)/'expected'; right = Path(tmp)/'actual'
            raw = expected(5); left.write_bytes(raw)
            for offset in (0, 1, 2, 3, 608, 609, 610, 611):
                damaged = bytearray(raw); damaged[offset] ^= 1; right.write_bytes(damaged)
                comparison = bytes_equal(left, right)
                self.assertFalse(comparison['passed'])
                self.assertEqual(comparison['different_bytes'], 1)
                self.assertEqual(comparison['first_mismatches'][0]['offset'], offset)
            for damaged in (raw[:-1], raw + b'\x00'):
                right.write_bytes(damaged)
                self.assertFalse(bytes_equal(left, right)['passed'])


if __name__ == '__main__':
    unittest.main()
