"""Independent stdlib decoder for the acquired noninterlaced RGBA8 PNGs.

Absolute colors below are post-acquisition observations, not predicted goldens.
"""
import hashlib,json,struct,sys,zlib
from pathlib import Path

def decode(b):
    if b[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('signature')
    pos=8; chunks=[]; payload=b''; size=None; ended=False
    while pos<len(b):
        if pos+12>len(b): raise ValueError('truncated chunk')
        n=struct.unpack('>I',b[pos:pos+4])[0]; typ=b[pos+4:pos+8]; data=b[pos+8:pos+8+n]
        if len(data)!=n or pos+12+n>len(b): raise ValueError('chunk size')
        crc=struct.unpack('>I',b[pos+8+n:pos+12+n])[0]
        if zlib.crc32(typ+data)&0xffffffff!=crc: raise ValueError('CRC')
        if typ==b'IHDR':
            if chunks or n!=13: raise ValueError('IHDR')
            w,h,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',data)
            if (depth,color,compression,filtering,interlace)!=(8,6,0,0,0) or (w,h)!=(128,96): raise ValueError('format')
            size=(w,h)
        elif typ==b'IDAT': payload+=data
        elif typ==b'IEND':
            if n or pos+12!=len(b): raise ValueError('IEND/trailing')
            ended=True
        elif typ not in (b'sRGB',b'eXIf',b'pHYs'): raise ValueError('unexpected chunk')
        chunks.append({'type':typ.decode(),'bytes':n}); pos+=n+12
    if not ended or size is None: raise ValueError('incomplete')
    dec=zlib.decompressobj(); packed=dec.decompress(payload)+dec.flush()
    if not dec.eof or dec.unused_data or dec.unconsumed_tail: raise ValueError('zlib framing')
    w,h=size; stride=w*4
    if len(packed)!=h*(stride+1): raise ValueError('scanline size')
    out=bytearray(); previous=bytearray(stride); filters={}
    for y in range(h):
        base=y*(stride+1); mode=packed[base]; filters[mode]=filters.get(mode,0)+1
        row=bytearray(packed[base+1:base+1+stride])
        for x in range(stride):
            a=row[x-4] if x>=4 else 0; b0=previous[x]; c=previous[x-4] if x>=4 else 0
            if mode==0: prediction=0
            elif mode==1: prediction=a
            elif mode==2: prediction=b0
            elif mode==3: prediction=(a+b0)//2
            elif mode==4:
                t=a+b0-c; ds=[abs(t-a),abs(t-b0),abs(t-c)]; prediction=[a,b0,c][ds.index(min(ds))]
            else: raise ValueError('filter')
            row[x]=(row[x]+prediction)&255
        out.extend(row); previous=row
    return bytes(out),chunks,filters

def main(root):
    root=Path(root); report={}; buffers={}
    from PIL import Image
    for label in ['primary','dark','light']:
        data=(root/(label+'.png')).read_bytes(); raw,chunks,filters=decode(data)
        pillow=Image.open(root/(label+'.png')).convert('RGBA').tobytes()
        if raw!=pillow: raise ValueError('independent decoder disagreement')
        pixels={tuple(raw[i:i+4]) for i in range(0,len(raw),4)}
        if len(pixels)!=1: raise ValueError('not uniform')
        report[label]={'decoded_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'observed_uniform_rgba':list(next(iter(pixels))),'chunks':chunks,'filters':filters,'pillow_complete_agreement':True}
        buffers[label]=raw
    if buffers['primary']!=buffers['dark']: raise ValueError('default/dark relation changed')
    a=buffers['dark']; b=buffers['light']
    differences=[sum(a[i]!=b[i] for i in range(channel,len(a),4)) for channel in range(4)]
    if differences!=[0,12288,0,0] or any(a[i]-b[i]!=9 for i in range(1,len(a),4)): raise ValueError('appearance relation')
    corrupt=bytearray((root/'dark.png').read_bytes()); corrupt[-1]^=1
    try: decode(bytes(corrupt))
    except ValueError: pass
    else: raise ValueError('bad CRC accepted')
    try: decode((root/'dark.png').read_bytes()+b'X')
    except ValueError: pass
    else: raise ValueError('trailing byte accepted')
    report['comparison']={'complete_decoded_bytes':sum(len(x) for x in buffers.values()),'default_equals_dark':True,'dark_vs_light_mismatches_per_channel':differences,'green_delta':9,'padding':'PNG decoded rows are tightly packed; no native allocation padding observed or claimed.','expectation_grade':'Post-acquisition relation independently decoded; no prior absolute-color prediction.'}
    return report
if __name__=='__main__': print(json.dumps(main(sys.argv[1]),indent=2))
