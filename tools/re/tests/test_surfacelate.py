import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfacelate import inspect
from reloop.surfacefailure import FLAGS,LATE_PHASES
from reloop.surface import expected


def fixture(phase):
    open_endpoint=phase=='late-ack-open'
    record={'phase':phase,'width':3,'height':2,'seed':7,'stride':128,'sender_pid':123,'receiver_pid':124,
            'mach_error':0x10004003,'peer_exit':43 if open_endpoint else 44,'peer_signal':0,
            'local_resource_refs_retained':1,'completion_accepted':False,'receiver_cleanup':'explicit',
            'late_ack_received':open_endpoint,**{key:True for key in FLAGS}}
    peer={'phase':phase,'sender_pid':123,'receiver_pid':124,'mach_error':0 if open_endpoint else 0x10000003,
          'resource_refs_before_cleanup':1,**{key:True for key in ['resource_name_removed','cf_reference_released','inbox_name_removed','reply_name_removed']}}
    raw=expected(3,2,128,7)
    return record,peer,{stage:raw for stage in ['imported','post-timeout','retained']}


class LateAckTests(unittest.TestCase):
    def test_open_and_revoked_endpoints_require_distinct_observations(self):
        for phase in LATE_PHASES:
            r,p,b=fixture(phase);self.assertTrue(inspect(r,p,(3,2,7),phase,b)['passed'])
            r['late_ack_received']=not r['late_ack_received'];self.assertEqual(inspect(r,p,(3,2,7),phase,b)['failure'],'late-receive')
            r,p,b=fixture(phase);p['mach_error']=123;self.assertEqual(inspect(r,p,(3,2,7),phase,b)['failure'],'peer-metadata-or-rights')

    def test_missing_peer_and_false_cleanup_cannot_certify_graceful_release(self):
        for key in ['resource_name_removed','cf_reference_released','inbox_name_removed','reply_name_removed']:
            r,p,b=fixture('late-ack-closed');p[key]=1
            self.assertEqual(inspect(r,p,(3,2,7),'late-ack-closed',b)['failure'],'peer-cleanup')
        r,p,b=fixture('late-ack-open');self.assertFalse(inspect(r,{},(3,2,7),'late-ack-open',b)['passed'])
        for key,value in [('sender_pid',125),('resource_refs_before_cleanup',True)]:
            r,p,b=fixture('late-ack-open');p[key]=value
            self.assertFalse(inspect(r,p,(3,2,7),'late-ack-open',b)['passed'])

    def test_every_post_timeout_stage_padding_and_actual_exit_required(self):
        for stage in ['imported','post-timeout','retained']:
            r,p,b=fixture('late-ack-open');raw=bytearray(b[stage]);raw[127]^=1;b[stage]=bytes(raw)
            self.assertEqual(inspect(r,p,(3,2,7),'late-ack-open',b)['failure'],'byte-mismatch')
        r,p,b=fixture('late-ack-open');self.assertEqual(inspect(r,p,(3,2,7),'late-ack-open',b,43)['failure'],'helper-exit')
        r['completion_accepted']=True;self.assertFalse(inspect(r,p,(3,2,7),'late-ack-open',b)['passed'])
