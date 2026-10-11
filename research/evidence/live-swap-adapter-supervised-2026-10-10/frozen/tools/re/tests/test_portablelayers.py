import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from reloop import portablelayers
from reloop.core import ROOT,load,validate_experiment
from reloop.verification import bytes_equal

class PortableLayerTests(unittest.TestCase):
    def test_independent_full_allocation(self):
        raw=portablelayers.expected(17,9,80,4,0)
        self.assertEqual(len(raw),16384)
        for row in range(9):
            self.assertEqual(raw[row*80:row*80+68],bytes((96,64,95,255))*17)
            self.assertEqual(raw[row*80+68:(row+1)*80],bytes([165])*12)
        self.assertEqual(raw[720:],bytes([195])*(16384-720))
        self.assertEqual(portablelayers.expected(64,64,256,1,1),bytes((0,0,255,255))*4096)
        for args in ((True,9,80,4,0),(17,9,80,4.0,0),(17,9,80,4,True),(0,9,80,4,0),(17,65,80,4,0),(17,9,67,4,0),(17,9,257,4,0),(17,9,80,20,0),(17,9,80,4,2)):
            with self.assertRaises(ValueError):portablelayers.expected(*args)

    def test_faults_include_alpha_padding_and_tail(self):
        raw=portablelayers.expected(17,9,80,8,0)
        with TemporaryDirectory() as tmp:
            a=Path(tmp)/'a';b=Path(tmp)/'b';a.write_bytes(raw)
            for offset in (0,3,68,79,707,719,720,16383):
                bad=bytearray(raw);bad[offset]^=1;b.write_bytes(bad)
                result=bytes_equal(a,b);self.assertFalse(result['passed']);self.assertEqual(result['different_bytes'],1)
            for bad in (raw[:-1],raw+b'\x00'):
                b.write_bytes(bad);self.assertFalse(bytes_equal(a,b)['passed'])

    def test_anchor_and_modes_before_execution(self):
        with TemporaryDirectory() as tmp,patch.object(portablelayers.Controller,'verify',return_value={'valid':True,'external_anchor_matches':False}),patch.object(portablelayers.subprocess,'run') as run:
            with self.assertRaises(ValueError):portablelayers.corpus(Path(tmp))
            run.assert_not_called()
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='portable-primary-layer-control');validate_experiment(e)
        for params in ({'layer_control':1},{'layer_control':True,'alpha_control':True},{'layer_control':True,'source_control':True},{'layer_control':True,'second_runtime':True}):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})

    def test_semantic_mutation_prerequisite_and_modes(self):
        with TemporaryDirectory() as tmp,patch.object(portablelayers.Controller,'verify',return_value={'valid':False}),patch.object(portablelayers.subprocess,'run') as run:
            with self.assertRaises(ValueError):portablelayers.mutants(Path(tmp))
            run.assert_not_called()
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='portable-primary-layer-algorithm-mutants');validate_experiment(e)
        for params in ({'layer_mutation_control':1},{'layer_mutation_control':True,'layer_control':True},{'layer_mutation_control':True,'second_runtime':True}):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})
