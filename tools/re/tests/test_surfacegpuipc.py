import base64
import copy
import json
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfacegpuipc import inspect
from reloop.surfaceipc import RECEIVER_FLAGS
from reloop.core import validate_experiment


class GPUMachTests(unittest.TestCase):
    def fixture(self):
        raw=b'\0\0\xff\xff'+b'\xa5'*12
        changed=bytearray(raw);changed[0]^=0x5a;final=bytearray(changed);final[1]^=0xa6
        record={'width':1,'height':1,'seed':0,'stride':8,'mode':'receiver-clean','receiver_exit':0,
                'surface_id':42,'snapshot_bytes':16,'sender_pid':100,'receiver_pid':200,
                'sender_send_refs_before':1,'sender_send_refs_after_copy':1,'sender_send_refs_after_exit':1,
                'sender_send_refs_after_release':0,'receiver_release':'explicit-port-and-cf',**{k:True for k in RECEIVER_FLAGS}}
        producer={'producer_pid':100,'surface_id':42,'width':1,'height':1,'stride':8,'allocation_bytes':16,
                  'callback_count':1,'callback_status':4,'status':4,'storage_mode':0,'unified_memory':True,'error_absent':True,
                  'before_base64':base64.b64encode(b'\xa5'*16).decode(),'after_base64':base64.b64encode(raw).decode()}
        payloads={'before':raw,'after-exit':bytes(changed),'after-owner-mutation':bytes(final),'port-only':bytes(final)}
        return record,producer,payloads

    def test_gpu_identity_completion_and_lifecycle_corruptions_reject(self):
        r,p,b=self.fixture();self.assertTrue(inspect(r,p,(1,1,0),'receiver-clean',b)['passed'])
        for k,v in [('producer_pid',101),('surface_id',43),('callback_count',True),('status',3),('callback_status',5),('error_absent',1),('allocation_bytes',15),('unified_memory',False)]:
            bad=copy.deepcopy(p);bad[k]=v;self.assertFalse(inspect(r,bad,(1,1,0),'receiver-clean',b)['passed'])
        for k,v in [('receiver_exit',23),('audit_peer_verified',False),('sender_send_refs_after_release',1),('receiver_pid',100),('snapshot_bytes',True)]:
            bad=copy.deepcopy(r);bad[k]=v;self.assertFalse(inspect(bad,p,(1,1,0),'receiver-clean',b)['passed'])
        self.assertFalse(inspect(r,{},(1,1,0),'receiver-clean',b)['passed'])

    def test_full_allocation_transfer_and_producer_faults_reject(self):
        r,p,b=self.fixture()
        for position in (0,4,8,15):
            bad=b.copy();raw=bytearray(bad['port-only']);raw[position]^=1;bad['port-only']=bytes(raw)
            self.assertFalse(inspect(r,p,(1,1,0),'receiver-clean',bad)['passed'])
            badp=p.copy();raw=bytearray(base64.b64decode(p['after_base64']));raw[position]^=1;badp['after_base64']=base64.b64encode(raw).decode()
            self.assertFalse(inspect(r,badp,(1,1,0),'receiver-clean',b)['passed'])
        bad=b.copy();del bad['before'];self.assertFalse(inspect(r,p,(1,1,0),'receiver-clean',bad)['passed'])

    def test_gpu_mode_rejects_unreviewed_sender_first(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        e=next(e for e in json.loads((root/'research/loop/campaign.json').read_text())['experiments'] if e['id']=='owned-gpu-surface-mach-receiver-exit')
        for value in ('sender',None):
            e['params']['exit_order']=value
            with self.assertRaises(ValueError):validate_experiment(e)

if __name__=='__main__':unittest.main()
