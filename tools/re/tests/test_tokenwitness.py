import pathlib
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.tokenwitness import WORDS,inspect,cache_projection
from reloop.discriminants import instructions


def fixture():
    bodies={**WORDS,0x1313b4:[0x90000010,0xf9400210,0xd61f0200]}
    return [''.join('%x: %s nop ignored\n'%(start+4*i,' '.join('%02x'%b for b in struct.pack('<I',w))) for i,w in enumerate(words)) for start,words in bodies.items()]


class Image:
    def __init__(self,texts):
        self.data=bytearray(0x140000)
        for text in texts:
            for site,(_,_,word) in instructions(text).items():struct.pack_into('<I',self.data,site,word)
    def file_offset(self,address):return address


class WitnessTests(unittest.TestCase):
    def verify(self,texts,image):
        # Import linkage has separate real-table mutation coverage in test_stubbind.
        with patch('reloop.tokenwitness.inspect_stub',return_value={'stub_instruction_bytes_compared':12,'import_symbol':'_swift_getTypeByMangledNameInContext2','import_library':'/usr/lib/swift/libswiftCore.dylib','import_pointer_address':'0x1234'}):return inspect(texts,image)
    def test_complete_body_bytes_and_gate(self):
        texts=fixture();f=self.verify(texts,Image(texts));self.assertEqual(f['compared_witness_instruction_bytes'],216);self.assertEqual(f['metadata_cache_cases'],65540);self.assertEqual(f['copy_table_slot_bytes'],16);self.assertEqual(f['destroy_table_slot_bytes'],8)
    def test_each_helper_byte_corruption_rejects(self):
        texts=fixture()
        for start,words in WORDS.items():
            for byte in range(4*len(words)):
                image=Image(texts);image.data[start+byte]^=1
                with self.assertRaises(ValueError):self.verify(texts,image)
    def test_each_instruction_mutation_even_matching_image_rejects(self):
        texts=fixture()
        for start,words in WORDS.items():
            for index,word in enumerate(words):
                bad=[text.replace('%x: %s'%(start+4*index,' '.join('%02x'%b for b in struct.pack('<I',word))),'%x: %s'%(start+4*index,' '.join('%02x'%b for b in struct.pack('<I',word^1)))) for text in texts]
                with self.assertRaises(ValueError):self.verify(bad,Image(bad))
    def test_missing_duplicate_and_extra_entries_reject(self):
        texts=fixture()
        for bad in [texts[:-1],texts+[texts[0]],[texts[0]+'ec10: 00 00 00 00 nop\n']+texts[1:]]:
            with self.assertRaises(ValueError):self.verify(bad,Image(bad))
    def test_zero_odd_and_nonzero_even_cache_controls(self):
        for value,expected in [(0,True),(1,True),(2,False),(3,True),(1<<63,False),((1<<64)-1,True)]:self.assertEqual(cache_projection(value),expected)
