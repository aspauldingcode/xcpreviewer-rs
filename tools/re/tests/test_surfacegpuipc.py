import base64
import copy
import json
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfacegpuipc import inspect,inspect_consumer,inspect_stall,inspect_reuse
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

    def test_consumer_full_buffer_and_completion_identity_faults_reject(self):
        r,p,b=self.fixture();initial=b'\x5c'*16384;after=b'\0\0\xff\xff'+initial[4:]
        c={'consumer_pid':200,'surface_id':42,'width':1,'height':1,'stride':256,'allocation_bytes':16384,
           'callback_count':1,'callback_status':4,'status':4,'source_storage_mode':0,'destination_storage_mode':0,
           'error_absent':True,'unified_memory':True,'before_base64':base64.b64encode(initial).decode(),'after_base64':base64.b64encode(after).decode()}
        self.assertTrue(inspect_consumer(c,r,(1,1,0))['passed'])
        for k,v in [('consumer_pid',100),('surface_id',43),('callback_count',True),('callback_status',3),('status',5),('stride',128),('allocation_bytes',True),('error_absent',1),('source_storage_mode',2)]:
            bad=c.copy();bad[k]=v;self.assertFalse(inspect_consumer(bad,r,(1,1,0))['passed'])
        for position in (0,4,255,256,16383):
            bad=c.copy();raw=bytearray(after);raw[position]^=1;bad['after_base64']=base64.b64encode(raw).decode()
            self.assertFalse(inspect_consumer(bad,r,(1,1,0))['passed'])
        self.assertFalse(inspect_consumer({},r,(1,1,0))['passed'])

    def test_consumer_flag_requires_reviewed_producer_and_boolean(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        e=next(e for e in json.loads((root/'research/loop/campaign.json').read_text())['experiments'] if e['id']=='owned-gpu-surface-peer-readback')
        for v in (1,'true',None):
            bad=copy.deepcopy(e);bad['params']['gpu_consumer_control']=v
            with self.assertRaises(ValueError):validate_experiment(bad)
        bad=copy.deepcopy(e);bad['params']['gpu_control']=False
        with self.assertRaises(ValueError):validate_experiment(bad)

    def test_stall_control_missing_types_and_pending_state_reject(self):
        good={'timeout_observed':True,'initial_wait_completion_accepted':False,
              'callbacks_before_release':0,'event_before_release':0,'event_after_release':1,
              'wait_deadline_ns':20000000,'status_before_release':2}
        self.assertTrue(inspect_stall(good))
        self.assertTrue(inspect_stall({**good,'status_before_release':3}))
        for key in good:
            bad=good.copy();del bad[key];self.assertFalse(inspect_stall(bad))
        for key,value in [('timeout_observed',1),('initial_wait_completion_accepted',0),
                          ('callbacks_before_release',1),('callbacks_before_release',False),
                          ('event_before_release',1),('event_after_release',0),
                          ('wait_deadline_ns',0),('status_before_release',4),('status_before_release',True)]:
            self.assertFalse(inspect_stall({**good,key:value}))

    def test_stall_flag_requires_consumer_and_boolean(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        e=next(e for e in json.loads((root/'research/loop/campaign.json').read_text())['experiments'] if e['id']=='owned-gpu-peer-event-timeout')
        for value in (1,'true',None):
            bad=copy.deepcopy(e);bad['params']['gpu_stall_control']=value
            with self.assertRaises(ValueError):validate_experiment(bad)
        bad=copy.deepcopy(e);bad['params']['gpu_consumer_control']=False
        with self.assertRaises(ValueError):validate_experiment(bad)

    def reuse_fixture(self):
        record,_,_=self.fixture();resources={'source':10,'destination':20,'queue':30,'event':40};frames=[]
        for generation,pixel in ((1,b'\xff\0\0\xff'),(2,b'\0\0\xff\xff')):
            frames.append({'generation':generation,'surface_id':42,'resources':resources.copy(),
                           'event_before_release':generation,'event_after_release':generation+1,
                           'wait_deadline_ns':20000000,'callbacks_before_release':0,'callback_count':1,
                           'callback_status':4,'status':4,'status_before_release':2,
                           'timeout_observed':True,'error_absent':True,
                           'source_after_base64':base64.b64encode(pixel+b'\xa5'*12).decode(),
                           'destination_after_base64':base64.b64encode(pixel+b'\x5c'*16380).decode()})
        return record,{'reuse_resources':resources,'reuse_frames':frames}

    def test_reuse_generation_identity_deadline_and_missing_frames_reject(self):
        record,value=self.reuse_fixture();self.assertTrue(inspect_reuse(value,record,(1,1,0))['passed'])
        for key,wrong in [('generation',2),('generation',True),('surface_id',43),('event_before_release',0),('event_after_release',1),('callback_count',2),('status',3),('timeout_observed',1),('error_absent',1),('status_before_release',4),('wait_deadline_ns',0)]:
            bad=copy.deepcopy(value);bad['reuse_frames'][0][key]=wrong;self.assertFalse(inspect_reuse(bad,record,(1,1,0))['passed'])
        bad=copy.deepcopy(value);bad['reuse_frames'].pop();self.assertFalse(inspect_reuse(bad,record,(1,1,0))['passed'])
        bad=copy.deepcopy(value);bad['reuse_frames'].reverse();self.assertFalse(inspect_reuse(bad,record,(1,1,0))['passed'])
        for token in (99,True):
            bad=copy.deepcopy(value);bad['reuse_frames'][0]['resources']['source']=token;self.assertFalse(inspect_reuse(bad,record,(1,1,0))['passed'])
        self.assertFalse(inspect_reuse({},record,(1,1,0))['passed'])
        for malformed in (['source','destination','queue','event'],None,True):
            bad=copy.deepcopy(value);bad['reuse_resources']=malformed;self.assertFalse(inspect_reuse(bad,record,(1,1,0))['passed'])

    def test_reuse_stale_frame_active_padding_and_tail_reject(self):
        record,value=self.reuse_fixture()
        bad=copy.deepcopy(value);bad['reuse_frames'][0]['destination_after_base64']=value['reuse_frames'][1]['destination_after_base64'];self.assertFalse(inspect_reuse(bad,record,(1,1,0))['passed'])
        for key,positions in [('source_after_base64',(0,4,8,15)),('destination_after_base64',(0,4,255,256,16383))]:
            for position in positions:
                bad=copy.deepcopy(value);data=bytearray(base64.b64decode(bad['reuse_frames'][0][key]));data[position]^=1;bad['reuse_frames'][0][key]=base64.b64encode(data).decode();self.assertFalse(inspect_reuse(bad,record,(1,1,0))['passed'])

    def test_reuse_flag_requires_stall_and_boolean(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        e=next(e for e in json.loads((root/'research/loop/campaign.json').read_text())['experiments'] if e['id']=='owned-gpu-event-frame-reuse')
        for value in (1,'true',None):
            bad=copy.deepcopy(e);bad['params']['gpu_reuse_control']=value
            with self.assertRaises(ValueError):validate_experiment(bad)
        bad=copy.deepcopy(e);bad['params']['gpu_stall_control']=False
        with self.assertRaises(ValueError):validate_experiment(bad)

    def test_gpu_mode_rejects_unreviewed_sender_first(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        e=next(e for e in json.loads((root/'research/loop/campaign.json').read_text())['experiments'] if e['id']=='owned-gpu-surface-mach-receiver-exit')
        for value in ('sender',None):
            e['params']['exit_order']=value
            with self.assertRaises(ValueError):validate_experiment(e)

if __name__=='__main__':unittest.main()
