"""Read-only, bounded arm64e cache-v5 authenticated stub resolution.

Format: Apple's dyld_cache_format.h and fixup-chains.h. No PAC signing,
loading, execution or private ABI calls. Unsupported layouts fail explicitly.
"""
from pathlib import Path
import struct,re,hashlib

def v5_code_pointer(page, first, offset, value_add):
    if len(page) not in (4096,16384) or first==0xffff or not 0<=first<=len(page)-8 or first%8 or offset%8 or not 0<=offset<=len(page)-8 or not 0<=value_add<1<<64:
        raise ValueError('Invalid/absent v5 page chain or slot')
    cursor=first
    for hops in range(len(page)//8):
        if not 0<=cursor<=len(page)-8:raise ValueError('Chain outside page')
        word=struct.unpack_from('<Q',page,cursor)[0]
        if cursor==offset:
            if not word>>63 or (word>>51)&1 or not (word>>50)&1:raise ValueError('Expected address-diverse IA authenticated code pointer')
            target=value_add+(word&((1<<34)-1))
            if target>=1<<64:raise ValueError('Target overflow')
            return {'target':target,'chain_hops':hops,'diversity':(word>>34)&65535,'address_diversity':True,'key':'IA','raw_word':hex(word)}
        step=(word>>52)&2047
        if cursor>offset or not step:raise ValueError('Slot is not a member of this page chain')
        cursor+=step*8
    raise ValueError('Page-chain traversal limit')

class Cache:
    def __init__(self,root):
        self.root=Path(root);self.maps=[];self.reads={}
        files=sorted(self.root.glob('dyld_shared_cache_arm64e*'))
        if len(files)>64:raise ValueError('Cache file count limit')
        for p in files:
            if p.suffix=='.map':continue
            with p.open('rb') as f:
                h=f.read(0x160)
                if not h.startswith(b'dyld_'):continue
                off,count=struct.unpack_from('<II',h,16)
                if count>64:raise ValueError('Mapping count limit')
                f.seek(off);d=f.read(count*32)
                for i in range(count):
                    a,size,fo,_,_=struct.unpack_from('<QQQII',d,i*32);self.maps.append((a,a+size,fo,p))
    def read(self,a,n):
        if not 0<n<=4*1024*1024:raise ValueError('Read size limit')
        rows=[m for m in self.maps if m[0]<=a and a+n<=m[1]]
        if len(rows)!=1:raise ValueError('Ambiguous/outside cache mapping')
        lo,hi,o,p=rows[0]
        with p.open('rb') as f:f.seek(o+a-lo);v=f.read(n)
        if len(v)!=n:raise ValueError('Truncated cache read')
        self.reads[(a,n)]={'address':hex(a),'bytes':n,'sha256':hashlib.sha256(v).hexdigest(),'cache_file':p.name,'file_offset':o+a-lo}
        return v
    def pointer(self,slot):
        lo,hi,o,p=next(m for m in self.maps if m[0]<=slot and slot+8<=m[1])
        with p.open('rb') as f:
            h=f.read(0x160);mo,mc=struct.unpack_from('<II',h,0x138)
            if mc>64:raise ValueError('Slide mapping count limit')
            f.seek(mo);d=f.read(mc*56);matches=[]
            for i in range(mc):
                row=struct.unpack_from('<6QII',d,56*i)
                if row[0]<=slot and slot+8<=row[0]+row[1]:matches.append(row)
            if len(matches)!=1:raise ValueError('No unique slide mapping')
            a,size,fo,so,ss,flags,mp,ip=matches[0]
            if (a,fo)!=(lo,o) or ss<24:raise ValueError('Slide mapping mismatch')
            f.seek(so);meta=f.read(24);version,ps,count,add=struct.unpack('<III4xQ',meta)
            if version!=5 or ps not in (4096,16384) or count*2+24>ss:raise ValueError('Unsupported slide layout')
            pi=(slot-a)//ps
            if pi>=count:raise ValueError('Page index outside starts')
            f.seek(so+24+pi*2);first=struct.unpack('<H',f.read(2))[0]
        origin=a+pi*ps;page=self.read(origin,ps);result=v5_code_pointer(page,first,slot-origin,add)
        result.update(slot=hex(slot),page_origin=hex(origin),page_start=first,page_size=ps,slide_version=5,value_add=hex(add),slide_file=p.name,slide_info_file_offset=so,slide_info_sha256=hashlib.sha256(meta).hexdigest(),cache_uuid=h[88:104].hex())
        return result
    def stub(self,address):
        from reloop.discriminants import pc_relative
        data=self.read(address,16);a,b,c,d=struct.unpack('<4I',data)
        if a&0x9f00001f!=0x90000011 or b&0xffc003ff!=0x91000231 or c!=0xf9400230 or d!=0xd71f0a11:raise ValueError('Unsupported authenticated stub')
        slot=pc_relative(a,address,True)+((b>>10)&4095);result=self.pointer(slot);result.update(stub=hex(address),stub_sha256=hashlib.sha256(data).hexdigest());return result
    def image(self,address):
        rows=[];path=None
        for line in (self.root/'dyld_shared_cache_arm64e.map').read_text().splitlines():
            if line.startswith('/'):path=line
            if '__TEXT ' in line:
                lo,hi=[int(x,16) for x in re.findall('0x[0-9A-Fa-f]+',line)]
                if lo<=address<hi:rows.append((path,lo,hi))
        if len(rows)!=1:raise ValueError('Target image map mismatch')
        return rows[0]
    def exports(self,imagebase):
        header=self.read(imagebase,32);magic,cpu,sub,kind,n,size,flags,res=struct.unpack('<8I',header)
        if magic!=0xfeedfacf or size>1024*1024 or n>size//8:raise ValueError('Unsupported image header')
        data=self.read(imagebase+32,size);o=0;link=None;trie=None;uuid=None
        for _ in range(n):
            cmd,cs=struct.unpack_from('<II',data,o)
            if cs<8 or o+cs>len(data):raise ValueError('Malformed load commands')
            if cmd==0x19 and data[o+8:o+24].split(b'\0')[0]==b'__LINKEDIT':link=struct.unpack_from('<QQQ',data,o+24)[::2]
            if cmd==0x80000033:trie=struct.unpack_from('<II',data,o+8)
            if cmd==0x80000022 and trie is None:trie=struct.unpack_from('<II',data,o+40)
            if cmd==0x1b:uuid=data[o+8:o+24].hex()
            o+=cs
        if link is None or trie is None:raise ValueError('No export trie')
        raw=self.read(link[0]+trie[0]-link[1],trie[1]);return raw,uuid

def export_names(raw,offset):
    def uleb(p):
        value=0
        for shift in range(0,70,7):
            if p>=len(raw):raise ValueError('Truncated ULEB')
            b=raw[p];p+=1;value|=(b&127)<<shift
            if not b&128:return value,p
        raise ValueError('ULEB limit')
    result=[];stack=[(0,'',frozenset())];nodes=0
    while stack:
        p,name,seen=stack.pop();nodes+=1
        if nodes>200000 or p in seen or len(name)>4096:raise ValueError('Export graph limit/cycle')
        start=p;size,p=uleb(p);end=p+size
        if end>=len(raw):raise ValueError('Export node bounds')
        if size:
            flags,q=uleb(p)
            if not flags&8:
                address,q=uleb(q)
                if q>end:raise ValueError('Export terminal bounds')
                if address==offset:result.append({'name':name,'flags':flags})
        count=raw[end];p=end+1
        for _ in range(count):
            stop=raw.find(b'\0',p)
            if stop<0:raise ValueError('Export edge bounds')
            edge=raw[p:stop].decode();child,p=uleb(stop+1);stack.append((child,name+edge,seen|{start}))
    return result
