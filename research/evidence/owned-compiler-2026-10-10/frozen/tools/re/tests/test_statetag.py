import pathlib
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.statetag import defined_symbol,tag_offset,inject,get_tag


class Image:
    def __init__(self):
        self.data=bytearray(512);self.name=b'owned_case_index'
        self.data[256:256+len(self.name)+1]=self.name+b'\0'
        struct.pack_into('<IBBHQ',self.data,64,0,15,1,0,0x1000)
        self.sections=[{'address':0x1000,'size':8,'disk':True}]
    def unpack(self,fmt,off):return struct.unpack_from(fmt,self.data,off)


class TagTests(unittest.TestCase):
    def symbol(self,m,count=1):
        with patch('reloop.statetag.tables',return_value=((64,count,256,64),(0,0),[])):return defined_symbol(m,'owned_case_index',0x1000)
    def test_defined_symbol_and_duplicate_reject(self):
        m=Image();self.assertEqual(self.symbol(m),0);m.data[80:96]=m.data[64:80]
        with self.assertRaises(ValueError):self.symbol(m,2)
    def test_symbol_type_name_address_and_section_faults_reject(self):
        for off,fmt,value in [(64,'<I',64),(68,'<B',1),(68,'<B',0xef),(69,'<B',0),(69,'<B',2),(72,'<Q',0x1004),(256,'<B',ord('X'))]:
            m=Image();struct.pack_into(fmt,m.data,off,value)
            with self.assertRaises(ValueError):self.symbol(m)
        m=Image();m.sections[0]['disk']=False
        with self.assertRaises(ValueError):self.symbol(m)
        m=Image();m.data[256:320]=b'X'*64
        with self.assertRaises(ValueError):self.symbol(m)
    def test_direct_tags_preserve_full_value_and_padding(self):
        for a in [0,24,64,65,66,256]:
            for b in [0,1,7,8,9,256]:
                offset=max(a,8*((b+7)//8)+57);before=bytes((i*31+17)%256 for i in range(offset+5))
                for tag in [0,1]:
                    actual=inject(before,a,b,tag);expected=before[:offset]+bytes([tag])+before[offset+1:]
                    self.assertEqual(actual,expected);self.assertEqual(get_tag(actual,a,b),tag);self.assertEqual(actual[-4:],before[-4:])
    def test_same_specialized_tag_offset_as_high_state_byte(self):self.assertEqual(tag_offset(24,8),65)
    def test_every_non_tag_byte_unchanged(self):
        before=bytes(range(70))
        for tag in [0,1]:
            after=inject(before,24,8,tag)
            for i in range(70):self.assertEqual(after[i],tag if i==65 else before[i])
    def test_extended_tags_and_wrong_input_domain_reject(self):
        for tag in [2,255,-1,True,1.0]:
            with self.assertRaises(ValueError):inject(bytes(70),24,8,tag)
        for a,b in [(-1,8),(24,4097),(24.0,8)]:
            with self.assertRaises(ValueError):tag_offset(a,b)
        bad=bytearray(70);bad[65]=2
        with self.assertRaises(ValueError):get_tag(bad,24,8)
    def test_missing_tag_byte_reject(self):
        for size in [0,64,65]:
            with self.assertRaises(ValueError):inject(bytes(size),24,8,0)
            with self.assertRaises(ValueError):get_tag(bytes(size),24,8)
