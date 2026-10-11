import pathlib
import struct
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.storageownership import project,field_names


class Reflection:
    def __init__(self):
        self.data=bytearray(256);struct.pack_into('<HHI',self.data,40,0,12,2)
        self.targets={116:32,56:160,68:176};self.names={160:'observers',176:'managedTokens'}
    def relative(self,address):return self.targets.get(address)
    def file_offset(self,address):
        if not 0<=address<len(self.data):raise ValueError('outside')
        return address
    def string(self,address):return self.names[address]


class OwnershipTests(unittest.TestCase):
    def test_aliases_and_nulls_preserve_call_multiplicity(self):
        for words in [(0,0,0),(7,7,7),(0,7,7)]:
            source=struct.pack('<QQQ',*words)
            for operation,event in [('copy','bridge_retain'),('destroy','bridge_release')]:self.assertEqual(project(source,operation)['events'],[(event,v) for v in words])
    def test_high_bit_words_remain_unsigned_and_ordered(self):
        source=struct.pack('<QQQ',0x8000000000000000,0xffffffffffffffff,1);p=project(source,'copy');self.assertEqual(p['copied_bytes'],source);self.assertEqual([v for _,v in p['events']],[0x8000000000000000,0xffffffffffffffff,1])
    def test_every_value_byte_preserved(self):
        for size in [8,24]:
            for position in range(size):
                source=bytearray(size);source[position]=255;self.assertEqual(project(source,'copy')['copied_bytes'],source)
    def test_noncontract_widths_and_operations_reject(self):
        for size in [0,7,9,16,23,25]:
            with self.assertRaises(ValueError):project(bytes(size),'copy')
        with self.assertRaises(ValueError):project(bytes(8),'free')
    def test_reflection_names_do_not_assign_word_offsets(self):self.assertEqual(field_names(Reflection(),100),['observers','managedTokens'])
    def test_reflection_bounds_missing_and_symbolic_names_reject(self):
        for off,fmt,value in [(40,'<H',1),(42,'<H',8),(44,'<I',0),(44,'<I',9)]:
            m=Reflection();struct.pack_into(fmt,m.data,off,value)
            with self.assertRaises(ValueError):field_names(m,100)
        for address in [116,56,68]:
            m=Reflection();del m.targets[address]
            with self.assertRaises(ValueError):field_names(m,100)
        m=Reflection();m.names[160]={'unresolved_symbolic_prefix_base64':'AA=='}
        with self.assertRaises(ValueError):field_names(m,100)
