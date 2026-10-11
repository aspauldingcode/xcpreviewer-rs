import tempfile
import unittest
from pathlib import Path
from reloop.mixedalpha import pixel, compare, MODELS, CASES, EVEN_MODEL
from reloop.core import load, ROOT, validate_experiment


class MixedAlphaTests(unittest.TestCase):
    def test_predictions_discriminate_before_native_observation(self):
        self.assertEqual(pixel(0,'straight'),bytes((128,64,192,128)))
        self.assertEqual(pixel(0,'premultiply-exact-alpha'),bytes((128,64,191,128)))
        self.assertEqual(pixel(0,'premultiply-quantized-alpha'),bytes((128,64,191,128)))
        for i in (4,6,7):
            self.assertGreater(len({pixel(i,m) for m in MODELS}),1)
        for m in MODELS:
            self.assertEqual(pixel(8,m),bytes(4))
            self.assertEqual(pixel(9,m),bytes((17,83,201,255)))
        for i in (True,-1,14,0.0):
            with self.assertRaises(ValueError): pixel(i,'straight')
        with self.assertRaises(ValueError): pixel(0,'fitted')

    def test_even_model_new_holdouts(self):
        self.assertEqual(pixel(3,EVEN_MODEL),bytes((51,154,230,191)))
        self.assertEqual(pixel(10,EVEN_MODEL),bytes((4,8,12,128)))
        self.assertEqual(pixel(11,EVEN_MODEL),bytes((8,12,16,128)))
        for i in (10,12,13):
            self.assertNotEqual(pixel(i,EVEN_MODEL),pixel(i,'premultiply-exact-alpha'))

    def test_complete_pixel_and_length_mutations(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); raw=pixel(9,'straight')*153; actual=out/'actual'
            for m in MODELS: (out/('expected-9-%s.rgba'%m)).write_bytes(raw)
            actual.write_bytes(raw)
            self.assertTrue(all(c['passed'] for c in compare(out,9,actual).values()))
            for offset in (0,1,2,3,608,609,610,611):
                damaged=bytearray(raw); damaged[offset]^=1; actual.write_bytes(damaged)
                result=compare(out,9,actual)
                self.assertTrue(all(not c['passed'] and c['different_bytes']==1 for c in result.values()))
            for damaged in (raw[:-1],raw+b'\x00'):
                actual.write_bytes(damaged)
                self.assertTrue(all(not c['passed'] for c in compare(out,9,actual).values()))

    def test_reviewed_mode_boolean_and_exclusive(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-mixed-alpha-oracle')
        validate_experiment(e)
        e['params']={'mixed_alpha_control':1}
        with self.assertRaises(ValueError): validate_experiment(e)
        for params in ({'mixed_alpha_control':True,'alpha_control':True},
                       {'mixed_even_control':1},
                       {'mixed_even_control':True,'mixed_alpha_control':True}):
            e['params']=params
            with self.assertRaises(ValueError): validate_experiment(e)
