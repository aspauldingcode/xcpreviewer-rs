import pathlib
import struct
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.stubbind import inspect

NAME='_swift_bridgeObjectRelease'
LIB='/usr/lib/swift/libswiftCore.dylib'


class Image:
    def __init__(self):
        data=bytearray(400);struct.pack_into('<I',data,16,3)
        struct.pack_into('<IIIIII',data,32,2,24,256,1,272,32)
        struct.pack_into('<II',data,56,0xb,80);struct.pack_into('<II',data,112,320,2)
        path=LIB.encode()+b'\0';size=((24+len(path)+7)//8)*8
        struct.pack_into('<III',data,136,0xc,size,24);data[160:160+len(path)]=path
        struct.pack_into('<IBBHQ',data,256,0,1,0,0x100,0);data[272:272+len(NAME)+1]=NAME.encode()+b'\0'
        struct.pack_into('<II',data,320,0,0)
        self.words=[0x90000010|(1<<29),0xf9400210,0xd61f0200]
        for i,w in enumerate(self.words):struct.pack_into('<I',data,352+4*i,w)
        self.data=bytes(data)
        self.sections=[{'address':0x1000,'size':12,'flags':8,'reserved1':0,'reserved2':12},{'address':0x2000,'size':8,'flags':6,'reserved1':1,'reserved2':0}]
    def unpack(self,fmt,off):return struct.unpack_from(fmt,self.data,off)
    def u32(self,off):return self.unpack('<I',off)[0]
    def file_offset(self,address):return 352+address-0x1000
    def text(self):return ''.join('%x: %s nop irrelevant\n'%(0x1000+4*i,' '.join('%02x'%b for b in struct.pack('<I',w))) for i,w in enumerate(self.words))


class StubBindingTests(unittest.TestCase):
    def verify(self,image):return inspect(image.text(),image,0x1000,NAME,LIB)
    def test_independent_stub_pointer_and_import_binding(self):
        f=self.verify(Image());self.assertTrue(f['release_symbol_binding_verified']);self.assertEqual(f['import_pointer_address'],'0x2000')
    def test_every_stub_byte_fault_rejects(self):
        for i in range(12):
            image=Image();data=bytearray(image.data);data[352+i]^=1;image.data=bytes(data)
            with self.assertRaises(ValueError):self.verify(image)
    def test_symbol_name_library_ordinal_pointer_and_table_faults_reject(self):
        for off,value in [(320,0x80000000),(324,1),(256,32),(260,0xf),(262,0),(272,ord('X')),(160,ord('X')),(116,0)]:
            image=Image();data=bytearray(image.data)
            if off in [320,324,256,116]:struct.pack_into('<I',data,off,value)
            elif off==262:struct.pack_into('<H',data,off,value)
            else:data[off]=value
            image.data=bytes(data)
            with self.assertRaises(ValueError):self.verify(image)
    def test_stub_register_fault_with_matching_bytes_rejects(self):
        image=Image();image.words[2]^=1<<5;data=bytearray(image.data);struct.pack_into('<I',data,360,image.words[2]);image.data=bytes(data)
        with self.assertRaises(ValueError):self.verify(image)
