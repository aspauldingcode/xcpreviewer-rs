import copy
import hashlib
import json
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfaceipc import inspect,inspect_receiver,PHASES,FLAGS,RECEIVER_PHASES,RECEIVER_FLAGS
from reloop.surface import expected


def fixture(mode='clean'):
    record={'width':3,'height':2,'seed':7,'stride':128,'mode':mode,'sender_exit':23 if mode=='abrupt' else 0,'sender_pid':123,'receiver_pid':124,**{k:True for k in FLAGS}}
    raw=expected(3,2,128,7);after=bytearray(raw);after[0]^=0x5a;final=bytearray(after);final[1]^=0xa6
    return record,dict(zip(PHASES,(raw,bytes(after),bytes(final))))


class SurfaceIPCTests(unittest.TestCase):
    def receiver_fixture(self,mode='receiver-clean'):
        r,p=fixture();r={k:v for k,v in r.items() if k not in FLAGS and k!='sender_exit'}
        r.update(mode=mode,receiver_exit=23 if mode=='receiver-abrupt' else 0,
                 receiver_release='process-teardown' if mode=='receiver-abrupt' else 'explicit-port-and-cf',
                 sender_send_refs_before=1,sender_send_refs_after_copy=1,sender_send_refs_after_exit=1,sender_send_refs_after_release=0)
        r.update({k:True for k in RECEIVER_FLAGS})
        return r,dict(zip(RECEIVER_PHASES,(p['before'],p['after-exit'],p['after-receiver-mutation'],p['after-receiver-mutation'])))

    def test_receiver_first_requires_all_four_exact_snapshots(self):
        r,p=self.receiver_fixture();self.assertTrue(inspect_receiver(r,(3,2,7),'receiver-clean',p)['passed'])
        for phase in RECEIVER_PHASES:
            changed=dict(p);raw=bytearray(changed[phase]);raw[127]^=1;changed[phase]=bytes(raw)
            self.assertEqual(inspect_receiver(r,(3,2,7),'receiver-clean',changed)['failure'],'byte-mismatch')
        p.pop('port-only');self.assertFalse(inspect_receiver(r,(3,2,7),'receiver-clean',p)['passed'])

    def test_receiver_first_rejects_wrong_right_counts_and_release_paths(self):
        for key,value in [('sender_send_refs_before',2),('sender_send_refs_after_copy',0),('sender_send_refs_after_exit',0),('sender_send_refs_after_release',1),('sender_send_refs_after_release',False)]:
            r,p=self.receiver_fixture();r[key]=value;self.assertFalse(inspect_receiver(r,(3,2,7),'receiver-clean',p)['passed'])
        r,p=self.receiver_fixture();r['receiver_release']='process-teardown'
        self.assertEqual(inspect_receiver(r,(3,2,7),'receiver-clean',p)['failure'],'release-path')

    def test_receiver_abrupt_exit_and_peer_identity_remain_distinct(self):
        r,p=self.receiver_fixture('receiver-abrupt');self.assertTrue(inspect_receiver(r,(3,2,7),'receiver-abrupt',p)['passed'])
        r['receiver_exit']=0;self.assertFalse(inspect_receiver(r,(3,2,7),'receiver-abrupt',p)['passed'])
        for value in (123,True,0):
            r,p=self.receiver_fixture();r['receiver_pid']=value
            self.assertEqual(inspect_receiver(r,(3,2,7),'receiver-clean',p)['failure'],'peer-identity')

    def test_receiver_first_cannot_replace_lifecycle_checks_with_truthy_values(self):
        for flag in RECEIVER_FLAGS:
            r,p=self.receiver_fixture();r[flag]=1;self.assertFalse(inspect_receiver(r,(3,2,7),'receiver-clean',p)['passed'])

    def test_published_receiver_first_golden_has_independent_expected_padding(self):
        root=pathlib.Path(__file__).resolve().parents[1]/'fixtures/SurfaceReceiverOracle'
        manifest=json.loads((root/'manifest.json').read_text());g=manifest['geometry']
        raw=expected(g['width'],g['height'],g['stride'],g['seed']);after=bytearray(raw);after[0]^=0x5a;final=bytearray(after);final[1]^=0xa6
        refs=dict(zip(RECEIVER_PHASES,(raw,bytes(after),bytes(final),bytes(final))))
        for entry in manifest['files']:
            data=(root/entry['path']).read_bytes();self.assertEqual(len(data),entry['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),entry['sha256'])
            self.assertEqual(data,refs[pathlib.Path(entry['path']).stem])

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
