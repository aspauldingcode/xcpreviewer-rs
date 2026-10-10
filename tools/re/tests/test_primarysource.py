import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from reloop import primarysource
from reloop.core import ROOT,load,validate_experiment

class PrimarySourceTests(unittest.TestCase):
    def test_whole_source_and_config(self):
        for case in range(20):
            for reverse in (0,1):
                cfg=primarysource.parse(primarysource.expression(case,reverse));self.assertEqual(cfg['alphas'],list((primarysource.CASES+primarysource.EXTRA_CASES)[case]));self.assertEqual(cfg['reverse'],reverse)
        base=primarysource.expression(4)
        self.assertEqual(primarysource.parse(base.replace('\n',';').replace('{;','{').replace(';}','}').rstrip(';')),primarysource.parse(base))
        cfg=primarysource.parse(primarysource.expression(4));self.assertIn('render_layers(17,9,stride,4,2,8,0)',primarysource.lower(cfg))
        for source in primarysource.rejected_sources():
            with self.assertRaises(ValueError):primarysource.parse(source)
        for value in (True,b'bad','x'*4097):
            with self.assertRaises(ValueError):primarysource.parse(value)
        for bad in ({**cfg,'width':True},{**cfg,'reverse':False},{**cfg,'alphas':[4,2,True]},{**cfg,'alphas':'4,2,8'},{**cfg,'extra':'bad'},{**cfg,'width':65}):
            with self.assertRaises(ValueError):primarysource.lower(bad)

    def test_independent_geometry_padding_tail(self):
        cfg=primarysource.parse(primarysource.expression(4));raw=primarysource.expected(cfg,80)
        self.assertEqual(raw[:68],bytes((96,64,95,255))*17);self.assertEqual(raw[68:80],bytes([165])*12);self.assertEqual(raw[720:],bytes([195])*(16384-720))
        for stride in (True,67,257):
            with self.assertRaises(ValueError):primarysource.expected(cfg,stride)

    def test_anchor_before_compiler_and_mode(self):
        with TemporaryDirectory() as tmp,patch.object(primarysource.Controller,'verify',return_value={'valid':True,'external_anchor_matches':False}),patch.object(primarysource.subprocess,'run') as run:
            with self.assertRaises(ValueError):primarysource.corpus(Path(tmp))
            run.assert_not_called()
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='portable-primary-source-subset');validate_experiment(e)
        for params in ({'primary_source_control':1},{'primary_source_control':True,'layer_control':True},{'primary_source_control':True,'source_control':True}):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})
