import copy
import pathlib
import struct
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.tokenlink import SITES,POINTERS,BRANCHES,CALLS,inspect
from reloop.discriminants import instructions


def fixture():
    codes={entry:{entry:('nop','',0)} for entry in SITES}
    for entry,sites in SITES.items():codes[entry].update({site:(op,args,0) for site,(op,args) in sites.items()})
    for entries,link in [(BRANCHES,False),(CALLS,True)]:
        for entry,sites in entries.items():
            for site,target in sites.items():codes[entry][site]=('bl' if link else 'b','ignored display',(0x94000000 if link else 0x14000000)|(((target-site)//4)&0x3ffffff))
    for entry,items in POINTERS.items():
        for site,reg,target in items:
            delta=((target&~4095)-(site&~4095))//4096;imm=delta&0x1fffff
            codes[entry][site]=('adrp','x%d, page'%reg,0x90000000|((imm&3)<<29)|((imm>>2)<<5)|reg)
            codes[entry][site+4]=('add','x%d, x%d, offset'%(reg,reg),0x91000000|((target&4095)<<10)|(reg<<5)|reg)
    for entry,site,target in [(0x41f2c,0x41f74,0x41fc4),(0xbeef0,0xbef44,0xbef68)]:
        op,args,_=codes[entry][site];codes[entry][site]=(op,args,(0xb4000000 if entry==0x41f2c else 0x54000001)|(((target-site)//4)<<5))
    return [''.join('%x: %s %s %s\n'%(site,' '.join('%02x'%b for b in struct.pack('<I',word)),op,args) for site,(op,args,word) in sorted(code.items())) for _,code in sorted(codes.items())]


class Image:
    def __init__(self,texts):
        self.offsets={};self.data=b''
        for text in texts:
            for site,(_,_,word) in instructions(text).items():
                for i in range(4):self.offsets[site+i]=len(self.data)+i
                self.data+=struct.pack('<I',word)
    def file_offset(self,site):return self.offsets[site]


class TokenLinkTests(unittest.TestCase):
    def test_encoded_association_with_full_selected_bytes(self):
        t=fixture();f=inspect(t,Image(t));self.assertTrue(f['token_link_verified']);self.assertEqual(f['encoded_direct_targets'],13)
        self.assertEqual(f['compared_instruction_bytes'],len(Image(t).data))
    def test_every_mapped_byte_corruption_rejects(self):
        t=fixture();image=Image(t)
        for i in range(len(image.data)):
            bad=Image(t);data=bytearray(bad.data);data[i]^=1;bad.data=bytes(data)
            with self.assertRaises(ValueError):inspect(t,bad)
    def test_capture_context_lock_guard_and_callback_faults_reject(self):
        t=fixture()
        for old,new in [('x0, x1, [x20, #0x10]','x0, x1, [x20, #0x18]'),('mov x20, x3','mov x20, x4'),('str x22, [sp, #0x20]','str x22, [sp, #0x28]'),('blr x23','blr x24'),('cmp w8, #0x1','cmp w8, #0x2'),('cbz x0, 0x41fc4','cbnz x0, 0x41fc4')]:
            bad=[s.replace(old,new) for s in t];self.assertNotEqual(bad,t)
            with self.assertRaises(ValueError):inspect(bad,Image(t))
    def test_encoded_pointer_fault_even_when_image_agrees_rejects(self):
        t=fixture();bad=t.copy();i=next(i for i,s in enumerate(bad) if s.startswith('419cc:'));line=bad[i].splitlines()[0];parts=line.split();parts[1]='03';bad[i]=bad[i].replace(line,' '.join(parts),1)
        with self.assertRaises(ValueError):inspect(bad,Image(bad))
    def test_missing_and_duplicate_entries_reject(self):
        t=fixture()
        for bad in [t[:-1],t+[t[0]],[t[0]+t[0].splitlines()[0]+'\n']+t[1:]]:
            with self.assertRaises(ValueError):inspect(bad,Image(t))

    def test_symbol_annotation_does_not_change_encoded_branch(self):
        t=fixture();bad=[s.replace('b.ne 0xbef68','b.ne 0xbef68 <display-name+0x78>') for s in t]
        self.assertTrue(inspect(bad,Image(t))['token_link_verified'])

    def test_each_direct_branch_fault_even_when_image_agrees_rejects(self):
        t=fixture()
        for entries in [BRANCHES,CALLS]:
            for sites in entries.values():
                for site in sites:
                    old=next(line for text in t for line in text.splitlines() if line.startswith('%x:'%site))
                    parts=old.split();parts[1]='%02x'%(int(parts[1],16)^1)
                    bad=[text.replace(old,' '.join(parts),1) for text in t]
                    with self.assertRaises(ValueError):inspect(bad,Image(bad))
