import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfacefailure import inspect,inspect_use,PHASES,FLAGS,ERRORS
from reloop.surface import expected


def fixture(phase):
    record={'phase':phase,'width':3,'height':2,'seed':7,'stride':128,'sender_pid':123,'receiver_pid':124,
            'completion_accepted':False,'mach_error':ERRORS[phase],
            'peer_exit':-1 if phase=='before-ack' else 41 if phase=='before-transfer' else 42,
            'peer_signal':9 if phase=='before-ack' else 0,'local_resource_refs_retained':1,
            'receiver_cleanup':'process-teardown' if phase=='before-ack' else 'explicit',**{k:True for k in FLAGS}}
    raw=expected(3,2,128,7);payloads={'retained':raw}
    if phase!='before-transfer':payloads['imported']=raw
    return record,payloads


class SurfaceFailureTests(unittest.TestCase):
    def test_use_state_is_not_local_right_count_or_final_reclamation(self):
        r={'phase':'use-state','width':3,'height':2,'seed':7,'stride':128,'local_use_counts':[0,0,1,1,0],'global_in_use':[0,1,1,1,0],'mach_port_name_removed':True,'cf_reference_retained':True}
        raw=expected(3,2,128,7);self.assertTrue(inspect_use(r,(3,2,7),raw)['passed'])
        for key,values in [('global_in_use',[0,0,1,1,0]),('local_use_counts',[0,1,1,1,0]),('global_in_use',[False,True,True,True,False])]:
            changed=dict(r);changed[key]=values;self.assertEqual(inspect_use(changed,(3,2,7),raw)['failure'],'use-state')

    def test_use_state_requires_retained_exact_bytes_and_successful_exit(self):
        r={'phase':'use-state','width':3,'height':2,'seed':7,'stride':128,'local_use_counts':[0,0,1,1,0],'global_in_use':[0,1,1,1,0],'mach_port_name_removed':True,'cf_reference_retained':True}
        raw=expected(3,2,128,7);changed=bytearray(raw);changed[127]^=1
        self.assertEqual(inspect_use(r,(3,2,7),changed)['failure'],'byte-mismatch')
        self.assertEqual(inspect_use(r,(3,2,7),raw,44)['failure'],'helper-exit')
        r['cf_reference_retained']=False;self.assertEqual(inspect_use(r,(3,2,7),raw)['failure'],'lifecycle')

    def test_success_shaped_json_never_overrides_nonzero_helper_exit(self):
        for phase in PHASES:
            r,p=fixture(phase);self.assertTrue(inspect(r,(3,2,7),phase,p)['passed'])
            self.assertEqual(inspect(r,(3,2,7),phase,p,43)['failure'],'helper-exit')

    def test_missing_or_altered_import_and_retained_padding_fail(self):
        for phase in PHASES:
            r,p=fixture(phase)
            for stage in p:
                missing=dict(p);missing.pop(stage);self.assertFalse(inspect(r,(3,2,7),phase,missing)['passed'])
                changed=dict(p);raw=bytearray(changed[stage]);raw[127]^=1;changed[stage]=bytes(raw)
                self.assertEqual(inspect(r,(3,2,7),phase,changed)['failure'],'byte-mismatch')
        r,p=fixture('before-transfer');p['imported']=p['retained'];self.assertFalse(inspect(r,(3,2,7),'before-transfer',p)['passed'])

    def test_fault_classes_and_exit_status_cannot_be_interchanged(self):
        for phase in PHASES:
            for key,value in [('mach_error',123),('peer_exit',0),('peer_signal',12),('local_resource_refs_retained',2),('local_resource_refs_retained',True)]:
                r,p=fixture(phase);r[key]=value;self.assertEqual(inspect(r,(3,2,7),phase,p)['failure'],'metadata-or-rights')

    def test_false_completion_and_real_cleanup_flags_required(self):
        for key in FLAGS:
            r,p=fixture('after-import');r[key]=1;self.assertFalse(inspect(r,(3,2,7),'after-import',p)['passed'])
        for value in (True,0,None):
            r,p=fixture('after-import');r['completion_accepted']=value;self.assertFalse(inspect(r,(3,2,7),'after-import',p)['passed'])
        r,p=fixture('before-ack');r['receiver_cleanup']='explicit';self.assertEqual(inspect(r,(3,2,7),'before-ack',p)['failure'],'cleanup-path')

    def test_same_peer_identity_cannot_attest_interprocess_faults(self):
        for value in (123,True,0):
            r,p=fixture('after-import');r['receiver_pid']=value;self.assertEqual(inspect(r,(3,2,7),'after-import',p)['failure'],'peer-identity')


if __name__=='__main__':unittest.main()
