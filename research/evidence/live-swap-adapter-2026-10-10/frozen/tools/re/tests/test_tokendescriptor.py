import pathlib
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.chained import rebase
from reloop.tokendescriptor import symbolic,span


class Image:
    def __init__(self):
        self.data=bytearray(4096)
        struct.pack_into('<I',self.data,16,2)
        struct.pack_into('<II',self.data,32,0x19,72)
        struct.pack_into('<QQQQ',self.data,56,0,4096,0,4096)
        struct.pack_into('<IIII',self.data,104,0x80000034,16,600,160)
        struct.pack_into('<7I',self.data,600,0,32,0,0,0,0,0)
        struct.pack_into('<II',self.data,632,1,8)
        struct.pack_into('<IHHQIH',self.data,640,24,4096,6,0,0,1)
        struct.pack_into('<H',self.data,662,256)
        struct.pack_into('<Q',self.data,256,384|(2<<51))
        struct.pack_into('<Q',self.data,264,400)
    def unpack(self,fmt,off):
        if off<0 or off+struct.calcsize(fmt)>len(self.data):raise ValueError('outside')
        return struct.unpack_from(fmt,self.data,off)
    def u32(self,off):return self.unpack('<I',off)[0]
    def file_offset(self,address):
        if not 0<=address<len(self.data):raise ValueError('unmapped')
        return address
    def context(self,address):return {'name':'State','kind':18,'parent':{'name':'Owner','kind':16}}


class DescriptorTests(unittest.TestCase):
    def test_verified_chain_membership_not_raw_mask(self):
        m=Image();self.assertEqual(rebase(m,264)['target'],400)
        for address in [260,268,384]:
            with self.assertRaises(ValueError):rebase(m,address)
    def test_fixup_kind_bounds_bind_reserved_and_chain_break_reject(self):
        for fmt,off,value in [('<I',600,1),('<I',632,2),('<I',640,23),('<H',644,2048),('<H',646,1),('<Q',648,4),('<H',662,0xffff),('<H',662,0x8000),('<Q',256,384),('<Q',264,400|(1<<63)),('<Q',264,400|(1<<44)),('<Q',264,400|(1<<36)),('<Q',264,8000)]:
            m=Image();struct.pack_into(fmt,m.data,off,value)
            with self.assertRaises(ValueError):rebase(m,264)
    def test_symbolic_embedded_nul_does_not_terminate_record(self):
        m=Image();m.data[800:807]=b'\x01'+struct.pack('<i',400-801)+b'G\0';r=symbolic(m,800,6)
        self.assertEqual(r['record_bytes'],7);self.assertEqual(r['operators'],'G');self.assertEqual(r['references'][0]['descriptor'],'0x190');self.assertEqual(r['references'][0]['context_path'],['Owner','State'])
    def test_indirect_reference_uses_verified_chain(self):
        m=Image();m.data[800:807]=b'\x02'+struct.pack('<i',264-801)+b'G\0';r=symbolic(m,800,6);self.assertEqual(r['references'][0]['descriptor'],'0x190')
        struct.pack_into('<Q',m.data,256,384)
        with self.assertRaises(ValueError):symbolic(m,800,6)
    def test_truncated_unsupported_missing_terminator_and_span_reject(self):
        for raw,length in [(b'\x01\x01\0',2),(b'\x03abcd\0',5),(b'GG',1),(b'\0\0',1)]:
            m=Image();m.data[800:800+len(raw)]=raw
            with self.assertRaises(ValueError):symbolic(m,800,length)
        m=Image()
        for address,length in [(4095,2),(0,0),(0,513)]:
            with self.assertRaises(ValueError):span(m,address,length)


def wrappers():
    from reloop.tokendescriptor import inspect
    m=Image();m.data.extend(b'\0'*(0xc0000-len(m.data)))
    names={400:'State',416:'ObserverAndTokenStorage',432:'ConcurrentInvalidationObserverBox',448:'ConcurrentTokenCallback',464:'InvalidationTrace',480:'IsolatedInvalidationObserverBox',496:'IsolatedTokenCallback'}
    def context(addr):
        if addr not in names:raise ValueError('unknown owned context')
        parent={'name':'PreviewsFoundationHost','kind':0}
        if addr==400:parent={'name':'FulfillOnceState','kind':16,'parent':parent}
        return {'name':names[addr],'kind':18 if addr==400 else 17,'parent':parent}
    m.context=context;texts=[]
    for entry,cache,desc,record,targets in [(0xbeea8,1000,800,1100,[400,416,432,448,464]),(0xbeecc,1008,900,1200,[400,416,480,496,464])]:
        struct.pack_into('<ii',m.data,desc,record-desc,30)
        raw=bytearray();positions=[0,6,12,17,23]
        for i,target in enumerate(targets):
            raw+=b'\x01'+struct.pack('<i',target-(record+positions[i]+1))
            raw+=b'y' if i in {0,1} else b'G' if i==3 else b''
        raw+=b'_G\0';m.data[record:record+31]=raw
        words=[0xa9bf7bfd,0x910003fd]
        for site,reg,target in [(entry+8,3,cache),(entry+16,4,desc)]:
            delta=((target&~4095)-(site&~4095))//4096;imm=delta&((1<<21)-1)
            words += [0x90000000|reg|((imm&3)<<29)|((imm>>2)<<5),0x91000000|reg|(reg<<5)|((target&4095)<<10)]
        words += [0x94000000|(((0xbeef0-(entry+24))//4)&0x3ffffff),0xa8c17bfd,0xd65f03c0]
        text=''
        for i,word in enumerate(words):
            struct.pack_into('<I',m.data,entry+4*i,word);text+='%x: %s nop ignored\n'%(entry+4*i,' '.join('%02x'%b for b in struct.pack('<I',word)))
        texts.append(text)
    return texts,m


class WrapperTests(unittest.TestCase):
    def test_owned_distinct_nominal_records(self):
        from reloop.tokendescriptor import inspect
        texts,m=wrappers();self.assertEqual(inspect(texts,m)['symbolic_reference_count'],10)
    def test_each_wrapper_byte_corruption_rejects(self):
        from reloop.tokendescriptor import inspect
        for entry in [0xbeea8,0xbeecc]:
            for byte in range(36):
                texts,m=wrappers();m.data[entry+byte]^=1
                with self.assertRaises(ValueError):inspect(texts,m)
    def test_changed_cache_descriptor_symbolic_identity_and_duplicates_reject(self):
        from reloop.tokendescriptor import inspect
        for address in [1000,1008,804,904,1100,1200,1130]:
            texts,m=wrappers();m.data[address]^=1
            with self.assertRaises(ValueError):inspect(texts,m)
        texts,m=wrappers()
        for bad in [texts[:1],texts+[texts[0]]]:
            with self.assertRaises(ValueError):inspect(bad,m)

    def test_duplicate_instruction_rows_reject(self):
        from reloop.tokendescriptor import inspect
        texts,m=wrappers();texts[0]+=texts[0].splitlines()[0]+"\n"
        with self.assertRaises(ValueError):inspect(texts,m)
