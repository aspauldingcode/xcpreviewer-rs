import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from reloop.mixedcallback import inspect_metadata,corpus,target_expected,active_pixels,LAYOUTS
from reloop.mixedquartz import prediction
from reloop.core import ROOT,load,validate_experiment
from reloop.verification import bytes_equal

META={'width':17,'height':9,'bits_per_component':8,'bits_per_pixel':32,
      'bytes_per_row':80,'bitmap_info':16385,'alpha_info':1,'data_bytes':720,
      'color_space':'kCGColorSpaceSRGB','callback_count':1,'reported_size':[17,9],'blend_mode':'normal'}


class MixedCallbackTests(unittest.TestCase):
    def test_geometry_events_and_blend_are_strict(self):
        raw=prediction(9,'rational-half-up');inspect_metadata(META,raw,0)
        inspect_metadata({**META,'blend_mode':'copy'},raw,1)
        for field,value in [('callback_count',True),('callback_count',0),('callback_count',2),
                            ('reported_size',[17,True]),('reported_size',[18,9]),
                            ('blend_mode','copy'),('color_space','kCGColorSpaceDisplayP3'),('bitmap_info',1)]:
            with self.assertRaises(ValueError):inspect_metadata({**META,field:value},raw,0)
        with self.assertRaises(ValueError):inspect_metadata(META,raw,True)
        with self.assertRaises(ValueError):inspect_metadata(META,raw[:-1],0)

    def test_full_target_pixels_padding_and_unmatched_extent(self):
        with tempfile.TemporaryDirectory() as tmp:
            left=Path(tmp)/'left';right=Path(tmp)/'right';raw=prediction(1,'rational-half-up');left.write_bytes(raw)
            for offset in (0,3,68,79,640,707,708,719):
                damaged=bytearray(raw);damaged[offset]^=1;right.write_bytes(damaged)
                self.assertFalse(bytes_equal(left,right)['passed'])
            for damaged in (raw[:-1],raw+b'\x00'):
                right.write_bytes(damaged);self.assertFalse(bytes_equal(left,right)['passed'])

    def test_anchor_rejection_before_any_native_compile(self):
        with tempfile.TemporaryDirectory() as tmp,patch('reloop.mixedcallback.Controller') as controller,patch('reloop.mixedcallback.subprocess.run') as run:
            controller.return_value.verify.return_value={'valid':True,'external_anchor_matches':False}
            with self.assertRaises(ValueError):corpus(Path(tmp))
            run.assert_not_called()

    def test_reviewed_boolean_and_separate_mode(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-mixed-alpha-render-callback');validate_experiment(e)
        for params in ({'mixed_callback_control':1},{'mixed_callback_control':True,'mixed_quartz_control':True},{'mixed_callback_layout_control':1},{'mixed_callback_layout_control':True,'mixed_callback_control':True}):
            e['params']=params
            with self.assertRaises(ValueError):validate_experiment(e)

    def test_layout_matrix_is_explicit_and_pixels_not_normalized(self):
        active=bytes((1,4,7,96))*153
        for index,(stride,info) in enumerate(LAYOUTS):
            raw=target_expected(active,stride)
            meta={**META,'bytes_per_row':stride,'data_bytes':stride*9,'bitmap_info':info,
                  'target_index':index,'requested_stride':stride,'requested_bitmap_info':info}
            inspect_metadata(meta,raw,index,True)
            self.assertEqual(active_pixels(raw,stride),active)
            with self.assertRaises(ValueError):inspect_metadata({**meta,'requested_stride':True},raw,index,True)
        for stride in (True,67,81):
            with self.assertRaises(ValueError):target_expected(active,stride)
            with self.assertRaises(ValueError):active_pixels(active,stride)
        # Padding never influences the separately extracted active bytes.
        padded=bytearray(target_expected(active,80));padded[-1]^=1
        self.assertEqual(active_pixels(padded,80),active)
        padded[2]^=1
        self.assertNotEqual(active_pixels(padded,80),active)
