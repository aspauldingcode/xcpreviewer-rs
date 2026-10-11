import pathlib
import struct
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.tokenconsume import START,STOP,RELEASE,inspect,decode,emulate
from reloop.core import validate_experiment,load,ROOT


def fixture(words=None):
    if words is None:
        words=[0x12000000|(7<<10)|(1<<5)|8,0x71000000|(1<<10)|(8<<5)|31,0x54000001|(2<<5),0x14000000|(((RELEASE-(START+12))//4)&0x3ffffff),0xd65f0000|(30<<5)]
    return ''.join('%x: %s nop irrelevant\n'%(START+4*i,' '.join('%02x'%b for b in struct.pack('<I',w))) for i,w in enumerate(words))


class Image:
    def __init__(self,text):
        from reloop.discriminants import instructions
        self.data=b''.join(struct.pack('<I',v[2]) for _,v in sorted(instructions(text).items()))
    def file_offset(self,address):return address-START


class ConsumerTests(unittest.TestCase):
    def test_all_flags_agree_and_compare_complete_bytes(self):
        text=fixture();facts=inspect(text,Image(text));self.assertEqual(facts['flag_cases'],65542);self.assertEqual(facts['compared_instruction_bytes'],20);self.assertEqual(facts['projected_release_cases'],258)
    def test_every_mapped_byte_fault_rejects(self):
        text=fixture()
        for i in range(20):
            image=Image(text);raw=bytearray(image.data);raw[i]^=1;image.data=bytes(raw)
            with self.assertRaises(ValueError):inspect(text,image)
    def test_each_instruction_mutation_with_matching_image_rejects(self):
        text=fixture();words=decode(text,Image(text))
        for i,mask in enumerate([1<<10,1<<10,1,1,1<<5]):
            bad=words.copy();bad[i]^=mask;t=fixture(bad)
            with self.assertRaises(ValueError):inspect(t,Image(t))
    def test_high_bits_are_masked_and_display_is_not_authority(self):
        text=fixture();words=decode(text,Image(text))
        for flag,expected in [(1,1),(0x101,1),(0x80000001,1),(2,0),(0xffffffff,0)]:self.assertEqual(emulate(words,flag)['release_calls'],expected)
        self.assertTrue(inspect(text.replace('nop irrelevant','wrong display'),Image(text))['consumer_verified'])
    def test_missing_duplicate_and_extra_rows_reject(self):
        text=fixture()
        for bad in ['\n'.join(text.splitlines()[:-1]),text+text.splitlines()[0]+'\n',text+'4265c: 00 00 00 00 nop\n']:
            with self.assertRaises(ValueError):inspect(bad,Image(text))
    def test_range_bounds_alignment_duplicates_and_flag_type_reject(self):
        e=next(e for e in load(ROOT/'research/loop/campaign.json')['experiments'] if e['id']=='native-token-result-consumer')
        for ranges in [[],['42649:4265c'],['42648:42648'],['42648:52648'],['no:4265c'],['42648:4265c']*2]:
            bad={**e,'params':{**e['params'],'ranges':ranges}}
            with self.assertRaises(ValueError):validate_experiment(bad)
        with self.assertRaises(ValueError):validate_experiment({**e,'params':{**e['params'],'cleanup_control':1}})
