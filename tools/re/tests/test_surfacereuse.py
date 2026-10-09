import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfacereuse import inspect,PHASES
from reloop.surface import expected


def fixture(mode='reuse'):
    same=mode=='reuse';r={'mode':mode,'width':3,'height':2,'seed':7,'next_seed':8,'stride':128,'receiver_exit':0,'sender_pid':123,'receiver_pid':124,'first_id':11,'second_id':11 if same else 12,'audit_peer_verified':True,'delayed_read_after_second_import':True,'rendezvous_removed':True}
    receiver={'receiver_pid':124,'first_id':r['first_id'],'second_id':r['second_id'],'audit_peer_verified':True,'port_names_equal':same,'first_refs_after_two_imports':2 if same else 1,'second_refs_after_first_release':1,'received_rights_released':True,'fixture_generations':[1,2]}
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

    def test_nonzero_exit_and_unverified_peer_cannot_promote_partial_success(self):
        r,c,p=fixture();self.assertEqual(inspect(r,c,(3,2,7),'reuse',p,51)['failure'],'helper-exit')
        c['audit_peer_verified']=1;self.assertEqual(inspect(r,c,(3,2,7),'reuse',p)['failure'],'release')
        r,c,p=fixture();r['receiver_pid']=123;c['receiver_pid']=123;self.assertEqual(inspect(r,c,(3,2,7),'reuse',p)['failure'],'peer-identity')


if __name__=='__main__':unittest.main()
