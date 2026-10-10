import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch
from reloop.linuxalpha import corpus,inspect
from reloop.portablealpha import expected,CASES
from reloop.core import digest


class LinuxAlphaTests(unittest.TestCase):
    def test_changed_anchor_rejects_before_container(self):
        with tempfile.TemporaryDirectory() as tmp,patch('reloop.linuxalpha.Controller') as controller,patch('reloop.linuxalpha.subprocess.run') as run:
            controller.return_value.verify.return_value={'valid':False}
            with self.assertRaises(ValueError):corpus(pathlib.Path(tmp))
            run.assert_not_called()

    def fixture(self,tmp):
        source=tmp/'source';source.mkdir();out=tmp/'out';out.mkdir();jobs=[];frames=[]
        # Typed verifier inventory: synthetic repeated native-backed geometry only.
        for i in range(108):
            n,bg=CASES[i%8];stride=80 if i%2 else 68;raw=expected(17,9,stride,n,bg)
            for folder,name in [(source,'expected-%d.rgba'%i),(source,'frame-%d.rgba'%i),(out,'frame-%d.rgba'%i)]:(folder/name).write_bytes(raw)
            (source/('native-%d.rgba'%(i%8))).write_bytes(b''.join(raw[y*stride:y*stride+68] for y in range(9)))
            jobs.append({'index':i,'w':17,'h':9,'stride':stride,'n':n,'bg':bg})
            frames.append({'index':i,'bytes':16384,'sha256':digest(out/('frame-%d.rgba'%i))})
        (source/'execution.json').write_text(json.dumps({'rows':jobs}))
        (source/'identities.json').write_text(json.dumps({'renderer_module':'renderer','checker_module':'checker'}))
        controls=[{'variant':v,'mutation':m,'mismatches':int(bool(m)),'passed':True} for v in range(8) for m in range(4)]
        (source/'wasmkit.json').write_text(json.dumps(controls));raw=expected(17,9,80,4,1);(source/'invalid-expected.rgba').write_bytes(raw)
        for i in range(12):(out/('invalid-%d.rgba'%i)).write_bytes(raw)
        result={'host_system':'Linux','architecture':'aarch64','wasmtime':'49.0.0','kernel':'unit fixture','imports':0,'frames':frames,'checker_rows':controls,'invalid_requests':12,'renderer_module_sha256':'renderer','checker_module_sha256':'checker'}
        return source,out,result

    def test_payload_padding_tail_invalid_and_checker_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source,out,result=self.fixture(pathlib.Path(directory))
            self.assertEqual(inspect(out,source,result)['allocation_bytes'],1769472)
            for offset in (0,3,612,16383):
                path=out/'frame-0.rgba';original=path.read_bytes();changed=bytearray(original);changed[offset]^=1;path.write_bytes(changed)
                result['frames'][0]['sha256']=digest(path) # Rehashing corruption cannot defeat independent comparison.
                with self.assertRaises(ValueError):inspect(out,source,result)
                path.write_bytes(original);result['frames'][0]['sha256']=digest(path)
            path=out/'frame-1.rgba';original=path.read_bytes();changed=bytearray(original);changed[68]^=1;path.write_bytes(changed);result['frames'][1]['sha256']=digest(path)
            with self.assertRaises(ValueError):inspect(out,source,result)
            path.write_bytes(original);result['frames'][1]['sha256']=digest(path)
            path=out/'invalid-0.rgba';original=path.read_bytes();path.write_bytes(b'wrong')
            with self.assertRaises(ValueError):inspect(out,source,result)
            path.write_bytes(original);result['checker_rows'][0]['variant']=False
            with self.assertRaises(ValueError):inspect(out,source,result)

    def test_host_and_module_identity_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source,out,result=self.fixture(pathlib.Path(directory))
            for key,value in [('host_system','Darwin'),('architecture','x86_64'),('renderer_module_sha256','changed'),('imports',False)]:
                changed={**result,key:value}
                with self.assertRaises(ValueError):inspect(out,source,changed)
