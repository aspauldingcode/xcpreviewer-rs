import copy
import unittest
from reloop.core import load,validate_experiment,ROOT
from reloop.primaryextent import CASES,EXTENTS
from reloop.primarysource import expression,parse,expected

class PrimaryExtentTests(unittest.TestCase):
    def test_independent_extents_padding_tail(self):
        for case in CASES:
            for reverse in (0,1):
                for w,h,stride in EXTENTS:
                    c=parse(expression(case,reverse,w,h));raw=expected(c,stride)
                    self.assertEqual(len(raw),16384)
                    for y in range(h):self.assertEqual(raw[y*stride+w*4:(y+1)*stride],b'\xa5'*(stride-w*4))
                    self.assertEqual(raw[stride*h:],b'\xc3'*(16384-stride*h))
        self.assertEqual(sum((16384-s*h)*2 for _ in CASES for _ in (0,1) for w,h,s in EXTENTS),1035264)
    def test_extent_flag_is_typed_and_exclusive(self):
        base=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-primary-extent-holdouts')
        validate_experiment(base)
        for value in (1,'true',None):
            e=copy.deepcopy(base);e['params']['primary_extent_control']=value
            with self.assertRaises(ValueError):validate_experiment(e)
        e=copy.deepcopy(base);e['params']['primary_layer_control']=True
        with self.assertRaises(ValueError):validate_experiment(e)
