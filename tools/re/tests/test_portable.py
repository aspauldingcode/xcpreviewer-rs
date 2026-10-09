import hashlib
import json
import pathlib
import sys
import unittest
from PIL import Image
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.portable import expected
from reloop.wasmkit import parse_result
from reloop.core import validate_experiment


class PortableTests(unittest.TestCase):
    def test_wasmkit_requires_one_typed_result(self):
        self.assertEqual(parse_result('[WasmTypes.Value.i32(0)]\n'),0)
        self.assertEqual(parse_result('[WasmTypes.Value.i32(1)]'),1)
        self.assertEqual(parse_result('[WasmTypes.Value.i32(-1)]'),0xffffffff)
        for text in ['', '0', '[WasmTypes.Value.i64(0)]', '[WasmTypes.Value.i32(0)]\n[WasmTypes.Value.i32(1)]','error\n[WasmTypes.Value.i32(0)]','[WasmTypes.Value.i32(4294967296)]','[WasmTypes.Value.i32(-2147483649)]']:
            with self.assertRaises(ValueError):parse_result(text)

    def test_second_runtime_parameter_requires_boolean(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        queue=json.loads((root/'research/loop/campaign.json').read_text())
        e=next(e for e in queue['experiments'] if e['id']=='portable-wasm-second-runtime-rejections')
        validate_experiment(e)
        for value in [1,'true',None]:
            e['params']['second_runtime']=value
            with self.assertRaises(ValueError):validate_experiment(e)

    def test_literals_match_published_independent_native_frames(self):
        root=pathlib.Path(__file__).resolve().parents[1]/'fixtures/SolidRendererOracle'
        manifest=json.loads((root/'manifest.json').read_text())
        for entry,variant in zip(manifest['files'],(2,3)):
            path=root/entry['path'];self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),entry['sha256'])
            with Image.open(path) as image:
                self.assertEqual(image.size,(320,160))
                self.assertEqual(image.convert('RGBA').tobytes(),expected(320,160,1280,variant))

    def test_padding_is_explicit_and_out_of_contract_requests_reject(self):
        raw=expected(3,2,16,2)
        self.assertEqual(raw[12:16],b'\xcd'*4);self.assertEqual(raw[28:32],b'\xcd'*4)
        self.assertEqual(len(raw),32)
        for args in [(0,160,1280,2),(321,160,1280,2),(320,161,1280,2),(320,160,1279,2),(320,160,1281,2),(320,160,1280,1)]:
            with self.assertRaises(ValueError):expected(*args)

if __name__=='__main__':unittest.main()
