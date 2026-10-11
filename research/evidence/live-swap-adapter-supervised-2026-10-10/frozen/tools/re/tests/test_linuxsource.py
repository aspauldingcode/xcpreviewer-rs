import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from reloop.linuxsource import inspect,corpus
from reloop.primarysource import parse,expression,expected
from reloop.core import atomic,digest,load,ROOT,validate_experiment


class LinuxSourceTests(unittest.TestCase):
    def fixture(self,tmp):
        source=tmp/'source';source.mkdir();out=tmp/'out';out.mkdir();jobs=[];checkers=[];frames=[];invalid=[];controls=[];aggregates=[];checker_invalid=[]
        for i in range(16):
            cfg=parse(expression(4,0,1 if i==14 else 64 if i==15 else 17,1 if i==14 else 64 if i==15 else 9))
            strides=[cfg['width']*4,min(256,cfg['width']*4+12)]
            module=source/('source-%d.wasm'%i);module.write_bytes(b'owned module fixture')
            checker=source/('checker-%d.wasm'%i);checker.write_bytes(b'owned checker fixture')
            ir=source/('source-%d.ll'%i);ir.write_bytes(b'owned IR fixture')
            (source/('source-%d.swift'%i)).write_text(expression(4,0,cfg['width'],cfg['height']))
            jobs.append({'ir_sha256':digest(ir),'index':i,'config':cfg,'strides':strides,'module_sha256':digest(module)})
            checkers.append({'job':i,'module_sha256':digest(checker)})
            for s,stride in enumerate(strides):
                raw=expected(cfg,stride);(source/('expected-%d-%d.raw'%(i,s))).write_bytes(raw)
                for repeat in range(2):
                    name='frame-%d-%d-%d.raw'%(i,s,repeat)
                    (source/name).write_bytes(raw);(out/name).write_bytes(raw)
                    if (cfg['width'],cfg['height'],stride)==(17,9,80):(source/('native-%d-%d-%d.raw'%(i,s,repeat))).write_bytes(raw)
                    frames.append({'job':i,'stride_index':s,'repeat':repeat,'bytes':16384,'sha256':digest(out/name)})
            for k,stride in enumerate((0,cfg['width']*4-1,257,0xffffffff)):
                (out/('invalid-%d-%d.raw'%(i,k))).write_bytes(expected(cfg,strides[0]));invalid.append({'job':i,'index':k,'stride':stride})
            rows=[{'stride_index':s,'mutation':m,'count':1 if m else 0} for s in range(2) for m in range(5)]
            atomic(source/('checker-v8-%d.json'%i),rows);controls.extend({'job':i,**r} for r in rows)
            aggregates.append({'job':i,'count':8,'module_sha256':digest(checker)})
            for k,(stride_index,mutation) in enumerate(((2,0),(0,5),(0xffffffff,0),(0,0xffffffff))):
                baseline=out/('checker-baseline-%d.raw'%i);baseline.write_bytes(bytes([195])*131072)
                (out/('checker-invalid-%d-%d.raw'%(i,k))).write_bytes(baseline.read_bytes())
                checker_invalid.append({'job':i,'index':k,'stride_index':stride_index,'mutation':mutation,'count':0xffffffff,'baseline_sha256':digest(baseline),'bytes':131072})
        atomic(source/'jobs.json',jobs);atomic(source/'wasmkit.json',checkers)
        return source,out,{'host_system':'Linux','architecture':'aarch64','wasmtime':'49.0.0','kernel':'unit fixture','imports':0,'fuel_per_call':10000000,'memory_limit_bytes':131072,'frames':frames,'invalid':invalid,'checker_invalid':checker_invalid,'controls':controls,'aggregates':aggregates,'renderer_hashes':[j['module_sha256'] for j in jobs]}

    def test_rehashed_corruption_and_no_write_controls(self):
        with TemporaryDirectory() as tmp:
            source,out,result=self.fixture(Path(tmp));self.assertEqual(inspect(out,source,result)['native_target_bytes'],20160)
            path=out/'frame-0-1-0.raw';raw=path.read_bytes()
            for offset in (0,3,68,79,719,720,16383):
                bad=bytearray(raw);bad[offset]^=1;path.write_bytes(bad);result['frames'][2]['sha256']=digest(path)
                with self.assertRaises(ValueError):inspect(out,source,result)
            path.write_bytes(raw);result['frames'][2]['sha256']=digest(path)
            (out/'invalid-0-0.raw').write_bytes(b'bad')
            with self.assertRaises(ValueError):inspect(out,source,result)
            (out/'invalid-0-0.raw').write_bytes((source/'expected-0-0.raw').read_bytes())
            path=out/'checker-invalid-0-0.raw';bad=bytearray(path.read_bytes());bad[-1]^=1;path.write_bytes(bad)
            with self.assertRaises(ValueError):inspect(out,source,result)

    def test_metadata_and_checker_fault_counts(self):
        with TemporaryDirectory() as tmp:
            source,out,r=self.fixture(Path(tmp))
            for key,value in [('host_system','Darwin'),('architecture','x86_64'),('imports',False),('fuel_per_call',True),('renderer_hashes',[]),('frames',r['frames'][:-1]),('aggregates',[])]:
                with self.assertRaises(ValueError):inspect(out,source,{**r,key:value})
            for name,key,value in [('frames','repeat',False),('controls','count',0),('aggregates','count',7),('invalid','stride',True),('checker_invalid','count',0)]:
                rows=[*r[name]];index=1 if name=='controls' else 0;rows[index]={**rows[index],key:value}
                with self.assertRaises(ValueError):inspect(out,source,{**r,name:rows})
            (source/'source-0.wasm').write_bytes(b'changed')
            with self.assertRaises(ValueError):inspect(out,source,r)

    def test_anchor_before_container_and_exclusive_mode(self):
        with TemporaryDirectory() as tmp,patch('reloop.linuxsource.Controller') as c,patch('reloop.linuxsource.subprocess.run') as run:
            c.return_value.verify.return_value={'valid':True,'external_anchor_matches':False}
            with self.assertRaises(ValueError):corpus(Path(tmp))
            run.assert_not_called()
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='linux-primary-source-subset');validate_experiment(e)
        for params in ({'primary_source_control':1},*[{'primary_source_control':True,k:True} for k in ('alpha_control','layer_control','layer_mutation_control')]):
            with self.assertRaises(ValueError):validate_experiment({**e,'params':params})
