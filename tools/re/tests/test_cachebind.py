"""Original synthetic controls for the documented v5 parser, no Apple data."""
import unittest,struct
from reloop.cachebind import v5_code_pointer,export_names

def pointer(target=0x1234,next=0,auth=1,addr=1,data_key=0):
    return target | (7<<34) | (addr<<50) | (data_key<<51) | (next<<52) | (auth<<63)
def page():
    data=bytearray(4096);struct.pack_into('<Q',data,8,pointer(next=2));struct.pack_into('<Q',data,24,pointer(0xabcdef));return data
class CacheBindingTests(unittest.TestCase):
    def test_exact_chain_membership_and_attributes(self):
        result=v5_code_pointer(page(),8,24,0x180000000)
        self.assertEqual(result['target'],0x180abcdef);self.assertEqual(result['chain_hops'],1);self.assertEqual(result['key'],'IA');self.assertEqual(result['diversity'],7)
    def test_nonmember_slot_is_rejected(self):
        with self.assertRaises(ValueError):v5_code_pointer(page(),8,16,0)
    def test_early_termination_is_rejected(self):
        data=page();struct.pack_into('<Q',data,8,pointer(next=0))
        with self.assertRaises(ValueError):v5_code_pointer(data,8,24,0)
    def test_absent_unaligned_or_outside_page_is_rejected(self):
        for first,offset,data in [(0xffff,24,page()),(4096,24,page()),(8,25,page()),(8,4096,page()),(8,24,bytes(100))]:
            with self.subTest(first=first,offset=offset,length=len(data)),self.assertRaises(ValueError):v5_code_pointer(data,first,offset,0)
    def test_authentication_profile_must_match(self):
        for kwargs in [{'auth':0},{'addr':0},{'data_key':1}]:
            data=page();struct.pack_into('<Q',data,24,pointer(**kwargs))
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v5_code_pointer(data,8,24,0)
    def test_target_overflow_and_negative_base_rejected(self):
        for base in [-1,2**64-1,2**64]:
            with self.subTest(base=base),self.assertRaises(ValueError):v5_code_pointer(page(),8,24,base)
    def test_export_exact_offset_not_nearest_symbol(self):
        # Root edge '_f' to terminal flags0/address16, empty children.
        trie=bytes([0,1])+b'_f\0'+bytes([6,2,0,16,0])
        self.assertEqual(export_names(trie,16),[{'name':'_f','flags':0}]);self.assertEqual(export_names(trie,17),[])
    def test_export_cycle_and_truncation_rejected(self):
        for data in [bytes([0,1])+b'_f\0'+bytes([0]),b'\x80',bytes([10,0])]:
            with self.subTest(data=data),self.assertRaises(ValueError):export_names(data,16)
    def test_export_reexport_not_misidentified_as_code(self):
        trie=bytes([0,1])+b'_f\0'+bytes([6,2,8,16,0])
        self.assertEqual(export_names(trie,16),[])
if __name__=='__main__':unittest.main()
