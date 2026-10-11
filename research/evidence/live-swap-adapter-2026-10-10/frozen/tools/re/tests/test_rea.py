import copy
import pathlib
import struct
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.rea import verify_pair,IMAGE_SHA,envelope
from reloop.core import source_files,ROOT,validate_experiment,load,evaluate


class Image:
    data=struct.pack('<I',0x94000000|((0xedf78-0x42634)//4))
    def file_offset(self,site):return 0


def fixtures():
    def ev(operation,result):
        return {'structuredContent':{'evidence_id':'ev_'+'a'*64,'subject':{'digest':{'sha256':IMAGE_SHA},'architecture':'arm64'},'provider':{'id':'ghidra','version':'12.1.2'},'analysis_profile':{'digest':'b'*64},'operation':operation,'normalized_result':result}}
    return ev('analyze_function',{'procedure':{'address':'00042604'},'pseudocode':'local output','assembly':['local output'],'outgoing_references':[{'source_address':'00042634','target_address':'000edf78','kind':{'call':True}}]}),ev('inspect_native_instruction',{'address':'00042634','status':'decoded','architecture':'arm64','length':4,'bytes':Image.data.hex(),'flow':{'kind':'call','computed':False,'conditional':False,'direct_destinations':['000edf78']}})


class ReaTests(unittest.TestCase):
    def verify(self,f,i):return verify_pair(f,i,Image(),0x42604,0x42634,0xedf78,IMAGE_SHA)
    def test_independent_encoded_target_and_bytes(self):
        f,i=fixtures();self.assertEqual(self.verify(f,i)['compared_bytes'],4)
    def test_identity_provider_operation_and_profile_mismatches(self):
        f,i=fixtures()
        for key,value in [('provider',{'id':'hopper'}),('subject',{'digest':{'sha256':'0'*64},'architecture':'arm64'}),('operation','other'),('evidence_id','invalid'),('analysis_profile',{'digest':'c'*64})]:
            bad=copy.deepcopy(i);bad['structuredContent'][key]=value
            with self.assertRaises(ValueError):self.verify(f,bad)
    def test_every_instruction_byte_rejects(self):
        f,i=fixtures()
        for p in range(4):
            bad=copy.deepcopy(i);raw=bytearray(Image.data);raw[p]^=1;bad['structuredContent']['normalized_result']['bytes']=raw.hex()
            with self.assertRaises(ValueError):self.verify(f,bad)
    def test_entry_reference_flow_and_missing_native_output_reject(self):
        f,i=fixtures()
        for key,value in [('procedure',{'address':'000428d0'}),('outgoing_references',[]),('assembly',[]),('pseudocode','')]:
            bad=copy.deepcopy(f);bad['structuredContent']['normalized_result'][key]=value
            with self.assertRaises(ValueError):self.verify(bad,i)
        bad=copy.deepcopy(i);bad['structuredContent']['normalized_result']['flow']['direct_destinations']=['000ee75c']
        with self.assertRaises(ValueError):self.verify(f,bad)
    def test_tool_error_and_missing_structured_result_reject(self):
        with self.assertRaises(RuntimeError):envelope({'isError':True})
        with self.assertRaises(ValueError):envelope({'content':[]})
    def test_pins_frozen_without_node_modules(self):
        files=source_files()
        self.assertIn(ROOT/'tools/re/rea/package-lock.json',files)
        self.assertIn(ROOT/'tools/re/rea/package.json',files)
        self.assertFalse(any('node_modules' in p.parts for p in files))

    def test_owned_flag_and_conflicting_target_reject(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='owned-rea-engine-control')
        for params in [{'owned_control':1},{'owned_control':True,'binary':'/tmp/unreviewed'},{'command':'other'}]:
            bad=copy.deepcopy(e);bad['params']=params
            with self.assertRaises(ValueError):validate_experiment(bad)

    def test_observed_ghidra_language_and_wrong_endian_reject(self):
        f,i=fixtures();i['structuredContent']['normalized_result']['architecture']='AARCH64:LE:64:AppleSilicon'
        self.assertEqual(self.verify(f,i)['compared_bytes'],4)
        i['structuredContent']['normalized_result']['architecture']='AARCH64:BE:64:AppleSilicon'
        with self.assertRaises(ValueError):self.verify(f,i)

    def test_campaign_accepts_verified_observations(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='owned-rea-engine-control')
        result={'observations':{'rea_verified':True,'provider_closed':True,'native_functions':1,'encoded_call_targets_verified':1,'compared_bytes':4}}
        self.assertEqual(evaluate(e['checks'],result)[0],'supports')
