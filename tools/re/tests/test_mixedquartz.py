import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from reloop.mixedquartz import prediction,native_expected,inspect_metadata,corpus
from reloop.core import ROOT,load,validate_experiment
from reloop.verification import bytes_equal

META={'width':17,'height':9,'bits_per_component':8,'bits_per_pixel':32,
      'bytes_per_row':80,'bitmap_info':16385,'alpha_info':1,'data_bytes':720,
      'color_space':'kCGColorSpaceSRGB','components':[17/255,83/255,201/255,1]}


class MixedQuartzTests(unittest.TestCase):
    def test_predeclared_models_and_full_padding(self):
        self.assertEqual(prediction(1,'rational-half-up')[:4],bytes((4,21,50,64)))
        self.assertEqual(prediction(10,'rational-half-up')[:4],bytes((3,5,7,128)))
        self.assertEqual(prediction(10,'rational-even')[:4],bytes((2,4,6,128)))
        raw=prediction(9,'rational-half-up');self.assertEqual(len(raw),720)
        self.assertEqual(native_expected(bytes((17,83,201,255))*153),raw)
        inspect_metadata(META,raw)
        for field,value in [('bitmap_info',1),('bytes_per_row',68),('components',[True,0,0,1]),('components',[float('nan'),0,0,1])]:
            with self.assertRaises(ValueError):inspect_metadata({**META,field:value},raw)
        for case in (True,-1,14):
            with self.assertRaises(ValueError):prediction(case,'rational-half-up')
        with self.assertRaises(ValueError):native_expected(bytes(611))

    def test_complete_pixel_padding_and_tail_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            left=Path(tmp)/'left';right=Path(tmp)/'right';raw=prediction(1,'rational-half-up');left.write_bytes(raw)
            for offset in (0,3,68,79,640,707,708,719):
                damaged=bytearray(raw);damaged[offset]^=1;right.write_bytes(damaged)
                self.assertFalse(bytes_equal(left,right)['passed'])
            for damaged in (raw[:-1],raw+b'\x00'):
                right.write_bytes(damaged);self.assertFalse(bytes_equal(left,right)['passed'])

    def test_changed_anchor_stops_before_compilation(self):
        with tempfile.TemporaryDirectory() as tmp, patch('reloop.mixedquartz.Controller') as controller, patch('reloop.mixedquartz.subprocess.run') as run:
            controller.return_value.verify.return_value={'valid':False,'external_anchor_matches':False}
            with self.assertRaises(ValueError):corpus(Path(tmp))
            run.assert_not_called()

    def test_strict_mode_and_exclusion(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-mixed-alpha-quartz-contrast');validate_experiment(e)
        for params in ({'mixed_quartz_control':1},{'mixed_quartz_control':True,'mixed_boundary_control':True}):
            e['params']=params
            with self.assertRaises(ValueError):validate_experiment(e)

    def test_public_color_mode_remains_separate(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-mixed-alpha-public-quartz-contrast')
        validate_experiment(e)
        for params in ({'mixed_public_quartz_control':1}, {'mixed_public_quartz_control':True,'mixed_quartz_control':True}, {'mixed_normal_quartz_control':1}, {'mixed_normal_quartz_control':True,'mixed_public_quartz_control':True}, {'mixed_blend_compare_control':1}):
            e['params']=params
            with self.assertRaises(ValueError):validate_experiment(e)

    def test_public_adapter_counts_and_all_variant_repeats(self):
        # Controlled fake acquisition is a verifier test, never native evidence.
        for damage in (False,True):
            with tempfile.TemporaryDirectory() as tmp, patch('reloop.mixedquartz.Controller') as constructor, patch('reloop.mixedquartz.subprocess.run') as run:
                root=Path(tmp);out=root/'out';out.mkdir();controller=constructor.return_value
                controller.verify.return_value={'valid':True,'external_anchor_matches':True}
                controller.runs=root/'runs'
                from reloop.mixedquartz import RUN
                native=controller.runs/RUN/'output';native.mkdir(parents=True)
                for case in range(14):
                    raw=prediction(case,'rational-half-up')
                    (native/('boundary-%d-0.png.cg.raw'%case)).write_bytes(b''.join(raw[r*80:r*80+68] for r in range(9)))
                def acquire(argv,**kwargs):
                    if argv[0]=='xcrun':return
                    prefix=Path(argv[1]);case=int(argv[2]);raw=prediction(case,'rational-half-up')
                    import json
                    for variant in range(4):
                        actual=bytearray(raw)
                        if damage and case==10 and prefix.name.endswith('-1') and variant==3:actual[719]^=1
                        prefix.with_name(prefix.name+'.%d.raw'%variant).write_bytes(actual)
                        prefix.with_name(prefix.name+'.%d.json'%variant).write_text(json.dumps(META))
                run.side_effect=acquire
                result=corpus(out,True)
                self.assertEqual(run.call_count,29)
                self.assertEqual(result['allocations'],112)
                self.assertEqual(result['repeat_equal_pairs'],55 if damage else 56)
                self.assertEqual(result['all_padding_unchanged'],not damage)
                self.assertEqual(result['public_inputs_equal'],not damage)

    def test_sealed_blend_contrast_checks_last_padding(self):
        from reloop.mixedquartz import blend_contrast,BLEND_RUNS
        with tempfile.TemporaryDirectory() as tmp,patch('reloop.mixedquartz.Controller') as constructor:
            root=Path(tmp);constructor.return_value.runs=root/'runs'
            constructor.return_value.verify.return_value={'valid':True,'external_anchor_matches':True}
            for rid,anchor in BLEND_RUNS:
                directory=root/'runs'/rid/'output';directory.mkdir(parents=True)
                for case in range(14):
                    for repeat in range(2):
                        for variant in range(4):
                            (directory/('quartz-%d-%d.%d.raw'%(case,repeat,variant))).write_bytes(prediction(case,'rational-half-up'))
            out=root/'out';out.mkdir()
            self.assertTrue(blend_contrast(out)['all_equal'])
            damaged=root/'runs'/BLEND_RUNS[1][0]/'output'/'quartz-13-1.3.raw'
            raw=bytearray(damaged.read_bytes());raw[-1]^=1;damaged.write_bytes(raw)
            result=blend_contrast(out)
            self.assertEqual(result['pairs'],112)
            self.assertEqual(result['compared_bytes'],80640)
            self.assertFalse(result['all_equal'])
