import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfacereuse import inspect,PHASES
from reloop.surface import expected


def fixture(mode='reuse'):
    same=mode=='reuse';r={'mode':mode,'width':3,'height':2,'seed':7,'next_seed':8,'stride':128,'receiver_exit':0,'sender_pid':123,'receiver_pid':124,'first_id':11,'second_id':11 if same else 12,'audit_peer_verified':True,'delayed_read_after_second_import':True,'rendezvous_removed':True,'sender_rights_released':True,'sender_aliases_released':True,'live_global_first':11,'live_global_second':11 if same else 12,'final_global_first':0,'final_global_second':0,'settled_global_first':0,'settled_global_second':0,'lookup_delay_us':100000}
    receiver={'receiver_pid':124,'first_id':r['first_id'],'second_id':r['second_id'],'audit_peer_verified':True,'port_names_equal':same,'first_refs_after_two_imports':2 if same else 1,'second_refs_after_first_release':1,'received_rights_released':True,'fixture_generations':[1,2],'first_lookup_after_release':r['first_id'] if same else 0,'remaining_lookup':r['second_id'],'retired_first_lookup':0,'retired_second_lookup':0}
    first=expected(3,2,128,7);second=expected(3,2,128,8);delayed=second if same else first
    return r,receiver,dict(zip(PHASES,(first,second,delayed,second,delayed)))


class SurfaceReuseTests(unittest.TestCase):
    def test_delayed_old_handle_expected_bytes_differ_by_storage_mode(self):
        for mode in ('reuse','separate'):
            r,c,p=fixture(mode);self.assertTrue(inspect(r,c,(3,2,7),mode,p)['passed'])
            p['delayed-first']=p['producer-first'] if mode=='reuse' else p['producer-next']
            self.assertEqual(inspect(r,c,(3,2,7),mode,p)['failure'],'byte-mismatch')

    def test_missing_stage_and_padding_mutation_cannot_pass(self):
        for phase in PHASES:
            r,c,p=fixture();p.pop(phase);self.assertFalse(inspect(r,c,(3,2,7),'reuse',p)['passed'])
            r,c,p=fixture();raw=bytearray(p[phase]);raw[127]^=1;p[phase]=bytes(raw)
            self.assertEqual(inspect(r,c,(3,2,7),'reuse',p)['failure'],'byte-mismatch')

    def test_resource_identity_and_import_right_counts_are_distinct(self):
        for key,value,failure in [('second_id',12,'resource-identity'),('first_refs_after_two_imports',1,'right-counts'),('second_refs_after_first_release',0,'right-counts'),('fixture_generations',[2,1],'fixture-generation')]:
            r,c,p=fixture();c[key]=value;self.assertEqual(inspect(r,c,(3,2,7),'reuse',p)['failure'],failure)
        r,c,p=fixture('separate');r['second_id']=r['first_id'];c['second_id']=r['first_id'];self.assertFalse(inspect(r,c,(3,2,7),'separate',p)['passed'])

    def test_retired_name_and_remaining_right_checks_fail_closed(self):
        for mode in ('reuse','separate'):
            for key in ('first_lookup_after_release','remaining_lookup','retired_first_lookup','retired_second_lookup'):
                for value in (None,True,999):
                    r,c,p=fixture(mode);c[key]=value
                    self.assertEqual(inspect(r,c,(3,2,7),mode,p)['failure'],'lookup-lifetime')

    def test_final_id_observable_requires_live_control_and_exact_types(self):
        for mode in ('reuse','separate'):
            for key in ('live_global_first','live_global_second','settled_global_first','settled_global_second'):
                for value in (None,True,999):
                    r,c,p=fixture(mode);r[key]=value
                    self.assertEqual(inspect(r,c,(3,2,7),mode,p)['failure'],'global-id-lifetime')
            r,c,p=fixture(mode);r['live_global_first']=0
            self.assertEqual(inspect(r,c,(3,2,7),mode,p)['failure'],'global-id-lifetime')
            r,c,p=fixture(mode);r['final_global_first']=r['first_id']
            self.assertTrue(inspect(r,c,(3,2,7),mode,p)['passed'])
            r['final_global_first']=True
            self.assertEqual(inspect(r,c,(3,2,7),mode,p)['failure'],'immediate-id-observation')
            r,c,p=fixture(mode);r['lookup_delay_us']=True
            self.assertEqual(inspect(r,c,(3,2,7),mode,p)['failure'],'lookup-delay')
            r,c,p=fixture(mode);r['sender_aliases_released']=False
            self.assertEqual(inspect(r,c,(3,2,7),mode,p)['failure'],'sender-release')

    def test_nonzero_exit_and_unverified_peer_cannot_promote_partial_success(self):
        r,c,p=fixture();self.assertEqual(inspect(r,c,(3,2,7),'reuse',p,51)['failure'],'helper-exit')
        c['audit_peer_verified']=1;self.assertEqual(inspect(r,c,(3,2,7),'reuse',p)['failure'],'release')
        r,c,p=fixture();r['receiver_pid']=123;c['receiver_pid']=123;self.assertEqual(inspect(r,c,(3,2,7),'reuse',p)['failure'],'peer-identity')


if __name__=='__main__':unittest.main()
