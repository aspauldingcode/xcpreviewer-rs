import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
from reloop import mixedorder

class MixedOrderTests(unittest.TestCase):
    def test_provider_layout(self):
        meta={'width':17,'height':9,'bits_per_component':8,'bits_per_pixel':32,'bytes_per_row':68,'bitmap_info':1,'alpha_info':1,'data_bytes':612,'color_space':'kCGColorSpaceSRGB'}
        mixedorder.inspect_snapshot(meta,bytes(612))
        for key,value in [('bytes_per_row',80),('bitmap_info',0x4001),('data_bytes',611),('width',True),('color_space','unknown')]:
            with self.assertRaises(ValueError):mixedorder.inspect_snapshot({**meta,key:value},bytes(612))
        for raw in (bytes(611),bytes(613)):
            with self.assertRaises(ValueError):mixedorder.inspect_snapshot(meta,raw)

    def test_anchor_before_compile(self):
        with TemporaryDirectory() as directory, patch.object(mixedorder.Controller,'verify',return_value={'valid':False}), patch.object(mixedorder.subprocess,'run') as run:
            with self.assertRaises(ValueError):mixedorder.corpus(Path(directory))
            run.assert_not_called()

    def test_byte_corruption_and_mode_rejection(self):
        from reloop.verification import bytes_equal
        from reloop.core import ROOT,load,validate_experiment
        with TemporaryDirectory() as directory:
            left=Path(directory)/'left';right=Path(directory)/'right';raw=bytes((1,4,8,96))*153;left.write_bytes(raw)
            for offset in (0,2,3,608,611):
                damaged=bytearray(raw);damaged[offset]^=1;right.write_bytes(damaged)
                self.assertFalse(bytes_equal(left,right)['passed'])
            for damaged in (raw[:-1],raw+b'\x00'):
                right.write_bytes(damaged);self.assertFalse(bytes_equal(left,right)['passed'])
        experiment=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-mixed-alpha-render-order')
        validate_experiment(experiment)
        for params in ({'mixed_order_control':1},{'mixed_order_control':True,'mixed_callback_control':True},{'mixed_order_export_control':True,'mixed_order_control':True}):
            with self.assertRaises(ValueError):validate_experiment({**experiment,'params':params})

    def test_export_anchor_before_decode(self):
        with TemporaryDirectory() as directory,patch.object(mixedorder.Controller,'verify',return_value={'valid':True,'external_anchor_matches':False}):
            with self.assertRaises(ValueError):mixedorder.export_contrast(Path(directory))
