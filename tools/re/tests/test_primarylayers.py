import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from reloop import primarylayers
from reloop.core import ROOT,load,validate_experiment
from reloop.verification import bytes_equal

META={'width':17,'height':9,'bits_per_component':8,'bits_per_pixel':32,'bytes_per_row':80,'bitmap_info':0x4001,'alpha_info':1,'data_bytes':720,'color_space':'kCGColorSpaceSRGB','callback_count':1,'reported_size':[17,9],'blend_mode':'normal','target_index':0,'rasterization_scale':1,'drawing_group':False,'layer_order':'forward'}

class PrimaryLayerTests(unittest.TestCase):
    def test_predeclared_source_predictions_discriminate(self):
        for m in primarylayers.MODELS:
            self.assertEqual(primarylayers.pixel(0,'forward',m),bytes((0,0,255,255)))
            self.assertEqual(primarylayers.pixel(1,'forward',m),bytes((255,0,0,255)))
            self.assertEqual(primarylayers.pixel(1,'reverse',m),bytes((0,0,255,255)))
            self.assertEqual(primarylayers.pixel(3,'forward',m),bytes(4))
        self.assertEqual(primarylayers.pixel(4,'forward','quantized-stage'),bytes((96,64,95,255)))
        self.assertEqual(primarylayers.pixel(4,'forward','exact-final'),bytes((96,64,96,255)))
        self.assertEqual(primarylayers.pixel(8,'forward','quantized-stage'),bytes((64,128,32,224)))
        self.assertEqual(primarylayers.pixel(8,'forward','exact-final'),bytes((64,128,32,223)))
        for args in ((True,'forward','exact-final'),(20,'forward','exact-final'),(0,'unknown','exact-final'),(0,'forward','unknown')):
            with self.assertRaises(ValueError):primarylayers.pixel(*args)

    def test_metadata_and_allocation_corruption(self):
        from reloop.mixedcallback import target_expected
        raw=target_expected(primarylayers.pixel(4,'forward','quantized-stage')*153,80)
        primarylayers.inspect_layer(META,raw,0,'forward')
        for key,value in [('drawing_group',0),('drawing_group',True),('target_index',True),('rasterization_scale',True),('rasterization_scale',2),('layer_order','reverse'),('callback_count',2)]:
            with self.assertRaises(ValueError):primarylayers.inspect_layer({**META,key:value},raw,0,'forward')
        with TemporaryDirectory() as tmp:
            left=Path(tmp)/'left';right=Path(tmp)/'right';left.write_bytes(raw)
            for offset in (0,2,3,68,79,707,708,719):
                bad=bytearray(raw);bad[offset]^=1;right.write_bytes(bad);self.assertFalse(bytes_equal(left,right)['passed'])
            for bad in (raw[:-1],raw+b'\x00'):
                right.write_bytes(bad);self.assertFalse(bytes_equal(left,right)['passed'])

    def test_anchor_and_mode(self):
        with TemporaryDirectory() as tmp,patch.object(primarylayers.Controller,'verify',return_value={'valid':True,'external_anchor_matches':False}),patch.object(primarylayers.subprocess,'run') as run:
            with self.assertRaises(ValueError):primarylayers.corpus(Path(tmp))
            run.assert_not_called()
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-primary-layer-composition');validate_experiment(e)
        for params in ({'primary_layer_control':1},{'primary_layer_control':True,'mixed_scale_control':True},{'primary_layer_holdout_control':1},{'primary_layer_holdout_control':True,'primary_layer_control':True}):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})
