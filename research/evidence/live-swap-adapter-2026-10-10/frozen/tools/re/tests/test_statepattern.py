import hashlib
import pathlib
import struct
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.statepattern import checked_body,layout_projection,copy_trailer


class Image:
    def __init__(self,data):self.data=data
    def file_offset(self,address):
        if not 0<=address<len(self.data):raise ValueError('unmapped')
        return address


def text(data):return ''.join('%x: %s nop ignored\n'%(i,' '.join('%02x'%v for v in data[i:i+4])) for i in range(0,len(data),4))


class PatternTests(unittest.TestCase):
    def test_owned_body_full_bytes_and_display_independence(self):
        raw=struct.pack('<II',0x91000400,0xd65f03c0);self.assertEqual(len(checked_body(text(raw),Image(raw),0,8,hashlib.sha256(raw).hexdigest())),2)
    def test_every_body_byte_mismatch_rejects(self):
        raw=struct.pack('<II',0x91000400,0xd65f03c0);h=hashlib.sha256(raw).hexdigest()
        for i in range(8):
            bad=bytearray(raw);bad[i]^=1
            with self.assertRaises(ValueError):checked_body(text(raw),Image(bad),0,8,h)
            with self.assertRaises(ValueError):checked_body(text(bad),Image(bad),0,8,h)
    def test_missing_extra_duplicate_body_and_mapping_reject(self):
        raw=struct.pack('<II',0x91000400,0xd65f03c0);t=text(raw);h=hashlib.sha256(raw).hexdigest()
        for bad in [t.splitlines()[0]+'\n',t+t.splitlines()[0]+'\n',t+'8: 00 00 00 00 nop\n']:
            with self.assertRaises(ValueError):checked_body(bad,Image(raw),0,8,h)
        with self.assertRaises(ValueError):checked_body(t,Image(raw[:4]),0,8,h)
    def test_layout_alignment_and_numeric_payload_selection(self):
        for a in [0,24,65,72,4096]:
            for b in [0,1,7,8,9,16,4096]:
                for tag in [0,1]:
                    f=layout_projection(a,b,tag);self.assertEqual(f['tag_offset'],max(a,((b+7)//8)*8+57));self.assertEqual(f['payload_index'],tag);self.assertEqual(f['copies_trailer'],bool(tag))
        self.assertEqual(layout_projection(24,8,1)['tag_offset'],65)
    def test_extended_tags_and_oversized_projection_domain_reject(self):
        for args in [(0,0,2),(0,0,-1),(4097,0,1),(0,-1,0),(1.0,0,0)]:
            with self.assertRaises(ValueError):layout_projection(*args)
    def test_entire_trailer_including_overlapping_tail(self):
        for position in range(57):
            source=bytearray(57);source[position]=255;self.assertEqual(copy_trailer(source),source)
        self.assertEqual(copy_trailer(bytes(range(57))),bytes(range(57)))
    def test_truncated_or_oversized_trailer_reject(self):
        for size in [0,41,48,56,58]:
            with self.assertRaises(ValueError):copy_trailer(bytes(size))
