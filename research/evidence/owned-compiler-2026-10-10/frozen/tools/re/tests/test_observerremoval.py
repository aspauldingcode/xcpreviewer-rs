import copy
import json
import pathlib
import struct
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.observerremoval import inspect,SITES,CALLS
from reloop.core import validate_experiment


class ConstantImage:
    def __init__(self):self.data=struct.pack('<QQ',0,1)
    def file_offset(self,address):return address-0x133190


def row(address,operation,args,word=0):
    raw=' '.join('%02x'%b for b in struct.pack('<I',word))
    return '%x: %s %s %s\n'%(address,raw,operation,args)


def fixture():
    result=[]
    for entry,sites in SITES.items():
        selected={entry:row(entry,'nop','')}
        for site,(operation,args) in sites.items():selected[site]=row(site,operation,args)
        for site,target in CALLS.get(entry,{}).items():selected[site]=row(site,'bl','0xdead',0x94000000|(((target-site)//4)&0x3ffffff))
        for body,site,reg in [(0x42604,0x4261c,9),(0xee834,0xee8bc,8)]:
            if entry==body:
                delta=(0x133000-(site&~4095))//4096;immediate=delta&0x1fffff
                word=0x90000000|((immediate&3)<<29)|((immediate>>2)<<5)|reg
                selected[site]=row(site,'adrp','x%d, 0x133000'%reg,word)
        result.append(''.join(selected[p] for p in sorted(selected)))
    return result


class ObserverRemovalTests(unittest.TestCase):
    def test_static_projection_uses_encoded_calls_and_full_constant(self):
        facts=inspect(fixture(),ConstantImage())
        self.assertTrue(facts['observer_removal_verified']);self.assertEqual(facts['sentinel_bytes'],16)
        self.assertEqual(facts['encoded_call_targets_verified'],12)

    def test_branch_storage_bitmap_count_and_shift_faults_reject(self):
        original=fixture()
        for old,new in [('b.eq 0xee018','b.ne 0xee018'),('w1, #0x0, 0xee7ec','w1, #0x1, 0xee7ec'),
                        ('cbz w0, 0xee824','cbnz w0, 0xee824'),('b.eq 0xee7f8','b.eq 0xee7e8'),
                        ('brk #0x1','nop #0x1'),('subs x8, x8, #0x1','subs x8, x8, #0x2'),
                        ('and x9, x10, x9','orr x9, x10, x9'),('str x8, [x19, #0x10]','str x8, [x19, #0x18]'),
                        ('lsl x2, x8, #3','lsl x2, x8, #2'),('str x23, [x19, #0x10]','str x22, [x19, #0x10]'),
                        ('b.hs 0xf8360','b.lo 0xf8360')]:
            texts=[t.replace(old,new) for t in original];self.assertNotEqual(texts,original)
            with self.assertRaises(ValueError):inspect(texts,ConstantImage())

    def test_missing_duplicate_and_encoded_target_faults_reject(self):
        texts=fixture()
        for bad in [texts[:-1],texts+[texts[0]],['']+texts[1:],[texts[0]+texts[0].splitlines()[0]+'\n']+texts[1:]]:
            with self.assertRaises(ValueError):inspect(bad,ConstantImage())
        for i,text in enumerate(texts):
            if ' bl ' in text:
                bad=texts.copy();line=next(l for l in text.splitlines() if ' bl ' in l);tokens=line.split();tokens[1]='ff' if tokens[1]!='ff' else '00';bad[i]=text.replace(line,' '.join(tokens),1)
                with self.assertRaises(ValueError):inspect(bad,ConstantImage())

    def test_every_constant_byte_and_truncated_mapping_reject(self):
        for position in range(16):
            image=ConstantImage();data=bytearray(image.data);data[position]^=1;image.data=bytes(data)
            with self.assertRaises(ValueError):inspect(fixture(),image)
        image=ConstantImage();image.data=image.data[:-1]
        with self.assertRaises(ValueError):inspect(fixture(),image)

    def test_dictionary_control_is_strict_boolean(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        e=next(e for e in json.loads((root/'research/loop/campaign.json').read_text())['experiments'] if e['id']=='native-observer-removal-control')
        for value in (1,'true',None):
            bad=copy.deepcopy(e);bad['params']['dictionary_control']=value
            with self.assertRaises(ValueError):validate_experiment(bad)

if __name__=='__main__':unittest.main()
