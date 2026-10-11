import base64
import copy
import json
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.surfacegpu import inspect,expected
from reloop.core import validate_experiment


class GPUSurfaceTests(unittest.TestCase):
    def fixture(self):
        # Independent literal 1x2 image, two padding bytes per row and tail.
        encode=lambda b:base64.b64encode(b).decode()
        red=b'\0\0\xff\xff\xa5\xa5'*2+b'\xa5'*4
        blue=b'\xff\0\0\xff\xa5\xa5'*2+b'\xa5'*4
        return {'width':1,'height':2,'stride':6,'allocation_bytes':16,'bytes_per_element':4,
                'pixel_format':0x42475241,'plane_count':0,'texture_storage_mode':0,
                'same_surface':True,'unified_memory':True,'before_base64':encode(b'\xa5'*16),'after_metal_drop_base64':encode(blue),
                'frames':[{'stage':i,'callback_count':1,'callback_status':4,'status':4,
                           'error_absent':True,'bytes_base64':encode(b)} for i,b in enumerate([red,red,blue])]}

    def test_full_allocation_and_color_change(self):
        f=self.fixture();self.assertTrue(inspect(f,(1,2))['passed'])
        self.assertEqual(expected(1,2,6,16,0),base64.b64decode(f['frames'][0]['bytes_base64']))
        for position in (0,4,6,12,15):
            bad=copy.deepcopy(f);raw=bytearray(base64.b64decode(bad['frames'][2]['bytes_base64']));raw[position]^=1
            bad['frames'][2]['bytes_base64']=base64.b64encode(raw).decode()
            self.assertFalse(inspect(bad,(1,2))['passed'])
        bad=copy.deepcopy(f);bad['frames'][2]['bytes_base64']=bad['frames'][0]['bytes_base64']
        self.assertFalse(inspect(bad,(1,2))['passed'])
        bad=copy.deepcopy(f);bad['after_metal_drop_base64']=bad['frames'][0]['bytes_base64']
        self.assertFalse(inspect(bad,(1,2))['passed'])

    def test_absent_wrong_type_failed_completion_and_identity_rejected(self):
        f=self.fixture()
        for key,value in [('stage',True),('callback_count',0),('callback_count',2),('status',3),('callback_status',5),('error_absent',1)]:
            bad=copy.deepcopy(f);bad['frames'][0][key]=value;self.assertFalse(inspect(bad,(1,2))['passed'])
        for key,value in [('same_surface',False),('texture_storage_mode',2),('allocation_bytes',True),('frames',[]),('before_base64','!')]:
            bad=copy.deepcopy(f);bad[key]=value;self.assertFalse(inspect(bad,(1,2))['passed'])
        self.assertFalse(inspect({},(1,2))['passed'])

    def test_gpu_flag_strict_boolean(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        e=next(e for e in json.loads((root/'research/loop/campaign.json').read_text())['experiments'] if e['id']=='owned-gpu-surface-completion')
        for value in (1,'true',None):
            e['params']['gpu_control']=value
            with self.assertRaises(ValueError):validate_experiment(e)

if __name__=='__main__':unittest.main()
