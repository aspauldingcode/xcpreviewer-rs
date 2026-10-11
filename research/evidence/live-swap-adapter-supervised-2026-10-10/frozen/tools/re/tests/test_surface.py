import base64
import hashlib
import json
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surface import expected,inspect


def record():
    raw=expected(3,2,64,7);after=bytearray(raw);after[0]^=0x5a
    return {'width':3,'height':2,'seed':7,'stride':64,'allocation_bytes':4096,'bytes_per_element':4,'pixel_format':0x42475241,'plane_count':0,'same_surface_id':True,'xpc_is_data':False,'before_base64':base64.b64encode(raw).decode(),'after_base64':base64.b64encode(after).decode()}


class SurfaceTests(unittest.TestCase):
    def test_published_native_golden_matches_independent_pattern_and_hashes(self):
        root=pathlib.Path(__file__).resolve().parents[1]/'fixtures/SurfaceOracle'
        manifest=json.loads((root/'manifest.json').read_text());g=manifest['geometry']
        for entry in manifest['files']:
            raw=(root/entry['path']).read_bytes()
            self.assertEqual(len(raw),entry['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
        raw=expected(g['width'],g['height'],g['stride'],g['seed'])
        self.assertEqual((root/'before.bin').read_bytes(),raw)
        after=bytearray(raw);after[0]^=0x5a
        self.assertEqual((root/'after.bin').read_bytes(),after)
        self.assertEqual(sum(bin(a^b).count('1') for a,b in zip(raw,after)),4)

    def test_padding_and_alias_mutation_are_exact_bytes(self):
        r=record();self.assertTrue(inspect(r,(3,2,7))['passed'])
        raw=bytearray(base64.b64decode(r['before_base64']));self.assertEqual(raw[12:64],b'\xa5'*52)
        self.assertEqual(raw[:4],bytes((7,60,113,255)))
        raw[13]^=1;r['before_base64']=base64.b64encode(raw).decode()
        self.assertFalse(inspect(r,(3,2,7))['passed'])

    def test_mutation_location_and_surface_identity_are_checked(self):
        r=record();r['after_base64']=r['before_base64'];self.assertFalse(inspect(r,(3,2,7))['passed'])
        r=record();r['same_surface_id']=1;self.assertFalse(inspect(r,(3,2,7))['passed'])
        r=record();r['xpc_is_data']=True;self.assertFalse(inspect(r,(3,2,7))['passed'])

    def test_geometry_plane_and_allocation_mismatch_fail_closed(self):
        for key,value in [('stride',11),('stride',True),('width',True),('height',3),('plane_count',1),('pixel_format',0),('allocation_bytes',127)]:
            r=record();r[key]=value;self.assertFalse(inspect(r,(3,2,7))['passed'],key)
        for args in [(0,1,64,7),(65,1,260,7),(3,17,64,7),(3,2,64,256)]:
            with self.assertRaises(ValueError):expected(*args)

    def test_truncation_or_invalid_base64_is_not_a_round_trip(self):
        r=record();r['before_base64']='!';self.assertFalse(inspect(r,(3,2,7))['passed'])
        r=record();r['before_base64']=base64.b64encode(b'\0'*12).decode();self.assertFalse(inspect(r,(3,2,7))['passed'])


if __name__=='__main__':unittest.main()
