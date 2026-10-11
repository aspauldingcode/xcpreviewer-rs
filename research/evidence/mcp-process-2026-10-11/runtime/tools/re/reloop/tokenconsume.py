"""Decode a finite ARM64 result-consumer body and emulate its numeric flag gate."""
import re
import struct
from reloop.discriminants import instructions
from reloop.tokenlink import branch

START=0x42648
STOP=0x4265c
RELEASE=0x1311c8


def signed(value,bits):return value-(1<<bits) if value&(1<<(bits-1)) else value


def decode(text,image):
    code=instructions(text)
    rows=re.findall(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+){4}\w',text,re.M)
    if len(rows)!=len(set(rows)) or set(code)!=set(range(START,STOP,4)):raise ValueError('Exact bounded consumer instructions required')
    words=[]
    for site in range(START,STOP,4):
        word=code[site][2];off=image.file_offset(site)
        if image.file_offset(site+3)!=off+3 or image.data[off:off+4]!=struct.pack('<I',word):raise ValueError('Consumer mapped bytes mismatch')
        words.append(word)
    logical,compare,conditional,tail,ret=words
    # W-register AND-immediate: N=0, immr=0, imms=7 => low-byte mask.
    if logical&0xffc00000!=0x12000000 or (logical&31,(logical>>5)&31,(logical>>16)&63,(logical>>10)&63)!=(8,1,0,7):raise ValueError('Consumer low-byte mask changed')
    if compare&0xffc0001f!=0x7100001f or (compare>>5)&31!=8 or (compare>>10)&4095!=1:raise ValueError('Consumer compare changed')
    destination=START+8+4*signed((conditional>>5)&0x7ffff,19)
    if conditional&0xff00001f!=0x54000001 or destination!=START+16:raise ValueError('Consumer skip condition changed')
    if branch(tail,START+12,False)!=RELEASE:raise ValueError('Consumer release tail target changed')
    if ret&0xfffffc1f!=0xd65f0000 or (ret>>5)&31!=30:raise ValueError('Consumer return changed')
    return words


def emulate(words,flag):
    # Execute only the decoded five-instruction projection; never call Apple code.
    pc=0;regs={1:flag&0xffffffff};equal=False
    for _ in range(5):
        word=words[pc]
        if pc==0:
            width=((word>>10)&63)+1;mask=(1<<width)-1
            regs[word&31]=regs[(word>>5)&31]&mask;pc+=1
        elif pc==1:
            equal=regs[(word>>5)&31]==((word>>10)&4095);pc+=1
        elif pc==2:pc=4 if not equal else 3
        elif pc==3:return {'tail_target':branch(word,START+12,False),'release_calls':1}
        else:return {'tail_target':None,'release_calls':0}
    raise ValueError('Consumer projection did not terminate')


def inspect(text,image):
    words=decode(text,image);values=list(range(65536))+[0x10000000,0x10000001,0x80000000,0x80000001,0xffffff00,0xffffffff]
    releases=0
    for flag in values:
        actual=emulate(words,flag);expected=1 if flag%256==1 else 0
        if actual['release_calls']!=expected or actual['tail_target']!=(RELEASE if expected else None):raise ValueError('Consumer projection contradicts independent flag oracle')
        releases+=expected
    return {'consumer_verified':True,'compared_instruction_bytes':20,'flag_cases':len(values),'projected_release_cases':releases,'release_tail_target':hex(RELEASE),'numeric_gate':'low8(flag)==1','scope':'Static byte-decoded projection only; source enum names, actual bridge ownership/deallocation, runtime invocation, transport and physical reclamation remain unverified.'}
