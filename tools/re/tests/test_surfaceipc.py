import copy
import hashlib
import json
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfaceipc import inspect,PHASES,FLAGS
from reloop.surface import expected


def fixture(mode='clean'):
    record={'width':3,'height':2,'seed':7,'stride':128,'mode':mode,'sender_exit':23 if mode=='abrupt' else 0,'sender_pid':123,'receiver_pid':124,**{k:True for k in FLAGS}}
    raw=expected(3,2,128,7);after=bytearray(raw);after[0]^=0x5a;final=bytearray(after);final[1]^=0xa6
    return record,dict(zip(PHASES,(raw,bytes(after),bytes(final))))


class SurfaceIPCTests(unittest.TestCase):
    def test_actual_bytes_required_at_all_three_lifetime_stages(self):
        record,payloads=fixture();self.assertTrue(inspect(record,(3,2,7),'clean',payloads)['passed'])
        for phase in PHASES:
            changed=copy.deepcopy(payloads);raw=bytearray(changed[phase]);raw[13]^=1;changed[phase]=bytes(raw)
            self.assertEqual(inspect(record,(3,2,7),'clean',changed)['failure'],'byte-mismatch')
        payloads.pop('after-exit');self.assertFalse(inspect(record,(3,2,7),'clean',payloads)['passed'])

    def test_same_process_or_integer_attestation_cannot_pass(self):
        for key in FLAGS:
            r,p=fixture();r[key]=1;self.assertFalse(inspect(r,(3,2,7),'clean',p)['passed'],key)
        for value in (123,True,0):
            r,p=fixture();r['receiver_pid']=value;self.assertEqual(inspect(r,(3,2,7),'clean',p)['failure'],'peer-identity')

    def test_clean_and_abrupt_exit_expectations_are_distinct(self):
        r,p=fixture('abrupt');self.assertTrue(inspect(r,(3,2,7),'abrupt',p)['passed'])
        r['sender_exit']=0;self.assertEqual(inspect(r,(3,2,7),'abrupt',p)['failure'],'metadata')
        r,p=fixture();r['mode']='abrupt';self.assertFalse(inspect(r,(3,2,7),'clean',p)['passed'])

    def test_geometry_and_padding_cannot_be_packed_or_coerced(self):
        for key,value in [('stride',12),('stride',True),('width',True),('height',3),('seed',8)]:
            r,p=fixture();r[key]=value;self.assertFalse(inspect(r,(3,2,7),'clean',p)['passed'],key)

    def test_published_handoff_golden_retains_exact_native_bytes(self):
        root=pathlib.Path(__file__).resolve().parents[1]/'fixtures/SurfaceIPCOracle'
        manifest=json.loads((root/'manifest.json').read_text());g=manifest['geometry']
        for entry in manifest['files']:
            raw=(root/entry['path']).read_bytes();self.assertEqual(len(raw),entry['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
        raw=expected(g['width'],g['height'],g['stride'],g['seed']);after=bytearray(raw);after[0]^=0x5a;final=bytearray(after);final[1]^=0xa6
        for phase,data in zip(PHASES,(raw,after,final)):self.assertEqual((root/(phase+'.bin')).read_bytes(),data)
        self.assertEqual(sum(bin(a^b).count('1') for a,b in zip(raw,final)),8)


if __name__=='__main__':unittest.main()
