import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from reloop import mixedscale
from reloop.mixedquartz import prediction
from reloop.core import ROOT,load,validate_experiment

META={'width':17,'height':9,'bits_per_component':8,'bits_per_pixel':32,'bytes_per_row':80,
      'bitmap_info':0x4001,'alpha_info':1,'data_bytes':720,'color_space':'kCGColorSpaceSRGB',
      'callback_count':1,'reported_size':[17,9],'blend_mode':'normal',
      'rasterization_scale':1,'target_index':0,'scale_order':'forward'}

class MixedScaleTests(unittest.TestCase):
    def test_scale_metadata(self):
        raw=prediction(9,'rational-half-up')
        for order in mixedscale.ORDERS:
            scales=mixedscale.SCALES if order=='forward' else mixedscale.SCALES[::-1]
            for index,scale in enumerate(scales):mixedscale.inspect_scale({**META,'scale_order':order,'target_index':index,'rasterization_scale':scale},raw,index,order)
        for k,v in [('rasterization_scale',True),('rasterization_scale',0),('rasterization_scale',2),('target_index',True),('scale_order','reverse'),('callback_count',2),('reported_size',[34,18])]:
            with self.assertRaises(ValueError):mixedscale.inspect_scale({**META,k:v},raw,0,'forward')
        for i,o in ((True,'forward'),(4,'forward'),(0,'unknown')):
            with self.assertRaises(ValueError):mixedscale.inspect_scale(META,raw,i,o)

    def test_anchors_before_compile(self):
        for result in ({'valid':False},{'valid':True,'external_anchor_matches':False}):
            with TemporaryDirectory() as tmp,patch.object(mixedscale.Controller,'verify',return_value=result),patch.object(mixedscale.subprocess,'run') as run:
                with self.assertRaises(ValueError):mixedscale.corpus(Path(tmp))
                run.assert_not_called()

    def test_reviewed_mode(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-mixed-alpha-rasterization-scale');validate_experiment(e)
        for params in ({'mixed_scale_control':1},{'mixed_scale_control':True,'mixed_callback_control':True},{'mixed_group_control':1},{'mixed_group_control':True,'mixed_scale_control':True}):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})
