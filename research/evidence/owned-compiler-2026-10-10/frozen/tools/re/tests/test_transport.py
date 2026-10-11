import base64
import copy
import hashlib
import json
import pathlib
import plistlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.xpc import inspect_result
from reloop.discriminants import interpret,instructions,pc_relative,returned_string
from reloop.core import validate_experiment
from reloop.planner import experiment


def result(value,sort=True):
    raw=plistlib.dumps(value,fmt=plistlib.FMT_BINARY,sort_keys=sort)
    encoded=base64.b64encode(raw).decode()
    return {'outcome':'decoded','round_trip_equal':True,'decoded_base64':encoded,'uv_data_base64':encoded,
            'xpc_tree':{'type':'dictionary','count':1,'items':{'data':{'type':'data','bytes':len(raw),'base64':encoded}}}}


class Image:
    def __init__(self,data=b''):self.data=data
    def file_offset(self,address):
        if not 0<=address<len(self.data):raise ValueError('Unmapped address')
        return address


class TransportTests(unittest.TestCase):
    def test_published_malformed_golden_has_exact_provenance_and_strict_parser_difference(self):
        root=pathlib.Path(__file__).resolve().parents[1]/'fixtures/XPCOracle'
        manifest=json.loads((root/'manifest.json').read_text())
        for entry in manifest['files']:
            raw=(root/entry['path']).read_bytes()
            self.assertEqual(len(raw),entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
        self.assertEqual(len(plistlib.loads((root/'minimal-input.plist').read_bytes())),1)
        self.assertEqual((root/'truncated-data.bin').read_bytes(),b'bplist00')
        with self.assertRaises(plistlib.InvalidFileException):
            plistlib.loads((root/'truncated-data.bin').read_bytes())
        self.assertEqual(manifest['expected']['xpc_decoded_value'],{})
        self.assertEqual(manifest['expected']['direct_data_decoded_value'],{})
        self.assertEqual(len(manifest['source_manifest_sha256']),64)

    def test_xpc_typed_round_trip_checks_actual_payload(self):
        value={'zero':-0.0,'bool':True,'unicode':'a\0🦀'}
        r=result(value);self.assertIsNone(inspect_result(r,value)['failure'])
        altered=result({'zero':0.0,'bool':True,'unicode':'a\0🦀'})
        self.assertEqual(inspect_result(altered,value)['failure'],'typed-mismatch')

    def test_round_trip_flag_cannot_substitute_for_decoding(self):
        r=result({'x':7})
        r['decoded_base64']=result({})['decoded_base64']
        self.assertEqual(inspect_result(r,{'x':7})['failure'],'typed-mismatch')
        r=result({'x':7});r['round_trip_equal']=1
        self.assertEqual(inspect_result(r,{'x':7})['failure'],'typed-mismatch')

    def test_capture_limit_is_not_a_native_semantic_failure(self):
        r=result({});r['xpc_tree']['items']['data']['truncated']=True
        self.assertEqual(inspect_result(r,{})['failure'],'capture-truncated')

    def test_semantic_equality_does_not_imply_payload_byte_equality(self):
        value={'z':1,'a':2};r=result(value,sort=False)
        r['uv_data_base64']=result(value,sort=True)['uv_data_base64']
        observed=inspect_result(r,value)
        self.assertTrue(observed['typed_equal']);self.assertEqual(observed['failure'],'byte-mismatch')

    def test_wrapper_type_length_and_base64_are_independent_checks(self):
        original=result({})
        r=copy.deepcopy(original);r['xpc_tree']['items']['data']['type']='string'
        self.assertEqual(inspect_result(r,{})['failure'],'payload-type')
        r=copy.deepcopy(original);r['xpc_tree']['items']['data']['bytes']+=1
        self.assertEqual(inspect_result(r,{})['failure'],'payload-length')
        r=copy.deepcopy(original);r['xpc_tree']['items']['data']['base64']='!'
        self.assertEqual(inspect_result(r,{})['failure'],'invalid-payload')
        r=copy.deepcopy(original);r['xpc_tree']['items']['extra']={}
        self.assertEqual(inspect_result(r,{})['failure'],'wrapper-shape')

    def test_xpc_adapter_does_not_accept_arbitrary_commands(self):
        e=experiment('owned-xpc-check','xpc_negative','Test malformed owned envelope.',{'command':'anything'},[{'path':'ok','equals':True}])
        with self.assertRaises(ValueError):validate_experiment(e)

    def test_pc_relative_addresses_match_native_instruction_vectors(self):
        self.assertEqual(pc_relative(0xd00001a9,0x887d4,True),0xbe000)
        self.assertEqual(pc_relative(0xb00001e8,0x887f4,True),0xc5000)
        self.assertEqual(pc_relative(0x1000008a,0x887dc,False),0x887ec)
        with self.assertRaises(ValueError):pc_relative(0,0x1000,True)

    def test_small_and_large_literal_forms_remain_separate(self):
        raw=b'layerHost'+b'\0'*7
        x0=int.from_bytes(raw[:8],'little');x1=int.from_bytes(raw[8:16],'little')|(0xe9<<56)
        self.assertEqual(returned_string(Image(),x0,x1),'layerHost')
        raw=b'previewInstances\0';image=Image(b'\0'*64+raw)
        self.assertEqual(returned_string(image,0xd000000000000010,0x8000000000000020),'previewInstances')
        with self.assertRaises(ValueError):returned_string(image,0,0)

    def test_interpreter_rejects_calls_unknown_reads_and_loops(self):
        for code,message in [
            ({0x100:('ldrb','w8, [x20]',0),0x104:('bl','0x108',0)},'Unsupported instruction'),
            ({0x100:('ldrb','w8, [x20]',0),0x104:('mov','x0, x9',0)},'unknown register'),
            ({0x100:('ldrb','w8, [x20]',0),0x104:('b','0x104',0)},'budget exceeded')]:
            with self.assertRaisesRegex(ValueError,message):interpret(Image(),code,0,maximum=4)

    def test_disassembly_parser_is_bounded_and_retains_machine_bytes(self):
        code=instructions(' 887dc:\t8a 00 00 10\tadr\tx10, #16\n')
        self.assertEqual(code[0x887dc],('adr','x10, #16',0x1000008a))
        with self.assertRaises(ValueError):instructions('not instructions')


if __name__=='__main__':unittest.main()
