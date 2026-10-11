import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from reloop.linuxlayers import inspect,corpus
from reloop.portablelayers import expected
from reloop.core import digest,atomic,load,ROOT,validate_experiment

class LinuxLayerTests(unittest.TestCase):
    def fixture(self,tmp):
        source=tmp/'source';source.mkdir();out=tmp/'out';out.mkdir();jobs=[];frames=[]
        for i in range(320):
            w,h,stride=((17,9,80),(1,1,8),(64,64,256),(31,7,132))[i%4]
            case=i%20;reverse=i%2;raw=expected(w,h,stride,case,reverse)
            for folder,name in ((source,'expected-%d.raw'%i),(source,'frame-%d.raw'%i),(out,'frame-%d.raw'%i)):(folder/name).write_bytes(raw)
            if (w,h,stride)==(17,9,80):(source/('native-full-%d.raw'%i)).write_bytes(raw)
            jobs.append({'index':i,'w':w,'h':h,'stride':stride,'variant':case,'reverse':reverse})
            frames.append({'index':i,'bytes':16384,'sha256':digest(out/('frame-%d.raw'%i))})
        atomic(source/'execution.json',{'rows':jobs});atomic(source/'identities.json',{'renderer_module':'renderer','checker_module':'checker'})
        controls=[{'variant':v,'mutation':m,'count':1 if m else 0} for v in range(40) for m in range(5)];atomic(source/'checker-v8.json',{'rows':controls})
        raw=expected(17,9,80,4,0);(source/'invalid-expected.raw').write_bytes(raw)
        for i in range(17):(out/('invalid-%d.raw'%i)).write_bytes(raw)
        result={'host_system':'Linux','architecture':'aarch64','wasmtime':'49.0.0','kernel':'unit fixture','imports':0,'frames':frames,'checker_rows':controls,'invalid_requests':17,'renderer_module_sha256':'renderer','checker_module_sha256':'checker','fuel_per_call':10000000,'memory_limit_bytes':131072}
        return source,out,result

    def test_corruption_rehash_cannot_defeat_expectations(self):
        with TemporaryDirectory() as tmp:
            source,out,result=self.fixture(Path(tmp));self.assertEqual(inspect(out,source,result)['allocation_bytes'],5242880)
            path=out/'frame-0.raw';original=path.read_bytes()
            for offset in (0,3,68,79,719,720,16383):
                bad=bytearray(original);bad[offset]^=1;path.write_bytes(bad);result['frames'][0]['sha256']=digest(path)
                with self.assertRaises(ValueError):inspect(out,source,result)
            path.write_bytes(original);result['frames'][0]['sha256']=digest(path)
            invalid=out/'invalid-0.raw';invalid.write_bytes(b'wrong')
            with self.assertRaises(ValueError):inspect(out,source,result)

    def test_host_bounds_module_and_inventory(self):
        with TemporaryDirectory() as tmp:
            source,out,result=self.fixture(Path(tmp))
            for key,value in [('host_system','Darwin'),('architecture','x86_64'),('imports',False),('renderer_module_sha256','wrong'),('fuel_per_call',True),('memory_limit_bytes',65536),('invalid_requests',True),('checker_rows',[*result['checker_rows'][:-1]])]:
                with self.assertRaises(ValueError):inspect(out,source,{**result,key:value})
            result['checker_rows'][0]['variant']=False
            with self.assertRaises(ValueError):inspect(out,source,result)

    def test_anchor_and_mode(self):
        with TemporaryDirectory() as tmp,patch('reloop.linuxlayers.Controller') as controller,patch('reloop.linuxlayers.subprocess.run') as run:
            controller.return_value.verify.return_value={'valid':True,'external_anchor_matches':False}
            with self.assertRaises(ValueError):corpus(Path(tmp))
            run.assert_not_called()
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='linux-primary-layer-control');validate_experiment(e)
        for params in ({'layer_control':1},{'layer_control':True,'alpha_control':True}):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})

    def test_semantic_mutant_metadata(self):
        from reloop.linuxlayers import inspect_mutants
        with TemporaryDirectory() as tmp:
            source=Path(tmp);targets=[];rows=[]
            for name in ('source-alpha-truncation','forward-layer-order'):
                controls=[{'variant':i,'mismatches':306 if i==8 else 0} for i in range(40)]
                atomic(source/(name+'.json'),{'rows':controls});targets.append({'mutation':name,'module_sha256':name+'-sha','v8_witness':306})
                rows.append({'mutation':name,'module_sha256':name+'-sha','rows':controls,'aggregate':0xffffffff,'witness':306})
            atomic(source/'mutations.json',targets)
            result={'host_system':'Linux','architecture':'aarch64','kernel':'unit fixture','wasmtime':'49.0.0','imports':0,'memory_limit_bytes':131072,'fuel_per_case':10000000,'fuel_per_aggregate':50000000,'mutants':rows}
            self.assertEqual(inspect_mutants(source,result)['native_cases'],80)
            for key,value in [('fuel_per_case',True),('imports',False),('host_system','Darwin')]:
                with self.assertRaises(ValueError):inspect_mutants(source,{**result,key:value})
            for key,value in [('witness',True),('aggregate',0),('module_sha256','changed')]:
                bad=[{**rows[0],key:value},rows[1]]
                with self.assertRaises(ValueError):inspect_mutants(source,{**result,'mutants':bad})
            rows[0]['rows'][0]['variant']=False
            with self.assertRaises(ValueError):inspect_mutants(source,result)
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='linux-primary-layer-algorithm-mutants')
        for params in ({'layer_mutation_control':1},{'layer_mutation_control':True,'layer_control':True},{'layer_mutation_control':True,'alpha_control':True}):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})
