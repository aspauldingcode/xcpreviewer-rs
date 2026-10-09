import hashlib
import json
import pathlib
import sys
import unittest
from PIL import Image
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.portable import expected


class PortableTests(unittest.TestCase):
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
