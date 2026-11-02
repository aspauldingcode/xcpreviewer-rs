from pathlib import Path
import struct
class Image:
 def __init__(self,path):
  self.path=Path(path);self.data=self.path.read_bytes();b=self.data;assert b[:4]==bytes.fromhex('cffaedfe');h=struct.unpack_from('<8I',b);assert h[1]==0x100000c and h[4]<512
  self.sections=[];self.uuid=None;tab=None;ind=None;at=32
  for _ in range(h[4]):
   cmd,size=struct.unpack_from('<II',b,at);assert size>=8 and at+size<=len(b)
   if cmd==0x1b:self.uuid=b[at+8:at+24].hex()
   if cmd==2:tab=struct.unpack_from('<4I',b,at+8)
   if cmd==0xb:ind=struct.unpack_from('<2I',b,at+56)
   if cmd==0x19:
    n=struct.unpack_from('<I',b,at+64)[0];assert 72+80*n<=size
    for i in range(n):
     a=at+72+80*i;name,seg,vm,length,off=struct.unpack_from('<16s16sQQI',b,a);flags,r1,r2=struct.unpack_from('<3I',b,a+64)
     self.sections.append({'name':name.split(b'\0')[0].decode(),'vm':vm,'length':length,'off':off,'flags':flags,'r1':r1,'r2':r2})
   at+=size
  assert self.uuid and tab and ind;so,ns,st,ss=tab;assert ns<1000000 and so+ns*16<=len(b) and st+ss<=len(b)
  strings=b[st:st+ss];self.symbols=[];self.named={}
  for i in range(ns):
   ix,ty,se,de,value=struct.unpack_from('<IBBHQ',b,so+16*i);assert ix<len(strings);end=strings.find(b'\0',ix);assert end>=ix;name=strings[ix:end].decode();self.symbols.append(name)
   if value:self.named.setdefault(value,[]).append(name)
  off,n=ind;assert off+4*n<=len(b);self.indirect=struct.unpack_from('<'+str(n)+'I',b,off)
 def read(self,address,size):
  rows=[s for s in self.sections if s['vm']<=address and address+size<=s['vm']+s['length']];assert len(rows)==1
  s=rows[0];o=s['off']+address-s['vm'];return self.data[o:o+size]
 def word(self,a):return struct.unpack('<I',self.read(a,4))[0]
 def branch(self,a):
  v=self.word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
 def resolve(self,a):
  for s in self.sections:
   if s['flags']&255==8 and s['vm']<=a<s['vm']+s['length']:
    assert s['r2'] and (a-s['vm'])%s['r2']==0;index=s['r1']+(a-s['vm'])//s['r2'];assert index<len(self.indirect);sym=self.indirect[index];assert sym<len(self.symbols);return {'kind':'import_stub','name':self.symbols[sym],'offset':hex(a)}
  return {'kind':'defined_symbol','names':self.named.get(a,[]),'offset':hex(a)}
