import base64
import unittest
from reloop.namereuse import inspect
from reloop.surface import expected

def fixture():
    r=dict(width=3,height=2,seed=7,stride=128,allocation=4096,first_id=11,second_id=12,live_lookup=11,retired_lookup=0,stale_lookup=0,previous_name_lookup=12,old_name=259,replacement_name=263,observations=[dict(name=263,current_id=12,stale_id=0,send_refs=1,removed=True) for _ in range(128)],ref_status=0,send_refs=1,release_status=0,name_removed=True)
    for k,seed in (('first',7),('second',8),('stale',8)):
        r[k+'_base64']=base64.b64encode(expected(3,2,128,seed)+bytes([0xa5])*3840).decode()
    return r

class NameReuseTests(unittest.TestCase):
    def test_positive_control(self):
        self.assertTrue(inspect(fixture(),(3,2,7))['passed'])
    def test_missing_or_bool_numeric_evidence_fails(self):
        for key in fixture():
            r=fixture();r.pop(key);self.assertFalse(inspect(r,(3,2,7))['passed'],key)
        for key in ('stale_lookup','retired_lookup','send_refs','old_name','allocation','stride'):
            r=fixture();r[key]=True;self.assertFalse(inspect(r,(3,2,7))['passed'],key)
    def test_stale_identity_cleanup_and_exit(self):
        for key,value in (('stale_lookup',11),('previous_name_lookup',0),('send_refs',2),('name_removed',False)):
            r=fixture();r[key]=value;self.assertFalse(inspect(r,(3,2,7))['passed'])
        self.assertFalse(inspect(fixture(),(3,2,7),7)['passed'])
    def test_each_full_allocation_phase_rejects_padding_tail_fault(self):
        for key in ('first','second','stale'):
            for offset in (0,127,4095):
                r=fixture();raw=bytearray(base64.b64decode(r[key+'_base64']));raw[offset]^=1
                r[key+'_base64']=base64.b64encode(raw).decode();self.assertFalse(inspect(r,(3,2,7))['passed'])

    def test_churn_stale_alias_when_exact_name_recurs(self):
        r=fixture();r['observations'][0]['name']=259;r['observations'][0]['stale_id']=12
        self.assertTrue(inspect(r,(3,2,7))['passed'])
        r['observations'][0]['stale_id']=0;self.assertFalse(inspect(r,(3,2,7))['passed'])
