import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from reloop.mixedboundary import layout, predicted_raw, export_prediction, corpus
from reloop.verification import bytes_equal
from reloop.core import ROOT, load, validate_experiment

META={'width':17,'height':9,'bits_per_component':8,'bits_per_pixel':32,
      'color_space':'kCGColorSpaceSRGB','bytes_per_row':80,'bitmap_info':8194,'alpha_info':2,'data_bytes':720}


class MixedBoundaryTests(unittest.TestCase):
    def test_independent_raw_and_relational_export(self):
        raw=predicted_raw(1,'half-up-exact',META)
        self.assertEqual(raw[:4],bytes((50,21,4,64)))
        self.assertEqual(export_prediction(META,raw),bytes((16,84,199,64))*153)
        self.assertEqual(export_prediction(META,predicted_raw(8,'half-up-exact',META)),bytes(612))
        self.assertNotEqual(predicted_raw(10,'half-up-exact',META),predicted_raw(10,'even-exact',META))

    def test_strict_metadata_and_unknown_layout_rejection(self):
        for field,value in [('width',True),('height',10),('bits_per_component',16),
                            ('bitmap_info',0x2102),('alpha_info',1),('bytes_per_row',67),
                            ('color_space','kCGColorSpaceDisplayP3'),('data_bytes',10**12),('data_bytes',719)]:
            m={**META,field:value}
            with self.assertRaises(ValueError):layout(m)
        default={**META,'bitmap_info':1,'alpha_info':1}
        self.assertEqual(predicted_raw(9,'half-up-exact',default)[:4],bytes((17,83,201,255)))
        with self.assertRaises(ValueError):layout(META,bytes(719))
        with self.assertRaises(ValueError):predicted_raw(True,'half-up-exact',META)
        with self.assertRaises(ValueError):predicted_raw(0,'fitted',META)

    def test_full_raw_pixel_padding_and_extent_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            left=Path(tmp)/'expected';right=Path(tmp)/'actual'
            raw=predicted_raw(1,'half-up-exact',META);left.write_bytes(raw)
            for offset in (0,3,68,79,640,707,708,719):
                damaged=bytearray(raw);damaged[offset]^=1;right.write_bytes(damaged)
                self.assertFalse(bytes_equal(left,right)['passed'])
            for damaged in (raw[:-1],raw+b'\x00'):
                right.write_bytes(damaged);self.assertFalse(bytes_equal(left,right)['passed'])

    def test_anchor_failure_precedes_compile(self):
        with tempfile.TemporaryDirectory() as tmp, patch('reloop.mixedboundary.Controller') as controller, patch('reloop.mixedboundary.subprocess.run') as run:
            controller.return_value.verify.return_value={'valid':True,'external_anchor_matches':False}
            with self.assertRaises(ValueError):corpus(Path(tmp))
            run.assert_not_called()

    def test_exclusive_reviewed_mode(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-mixed-alpha-export-boundary')
        validate_experiment(e)
        for params in ({'mixed_boundary_control':1},{'mixed_boundary_control':True,'mixed_even_control':True}):
            e['params']=params
            with self.assertRaises(ValueError):validate_experiment(e)
