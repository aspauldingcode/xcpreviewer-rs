"""Owned minimal import-free memory lifecycle probe, not a renderer."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent

def u(n):
    out=bytearray()
    while True:
        b=n&127;n>>=7;out.append(b|(128 if n else 0))
        if not n:return bytes(out)
def section(kind,raw):return bytes([kind])+u(len(raw))+raw

def module():
    types=b'\2\x60\2\x7f\x7f\0\x60\1\x7f\1\x7f'
    exports=b'\3'
    for name,kind,index in [('memory',2,0),('store8',0,0),('grow',0,1)]:
        raw=name.encode();exports+=u(len(raw))+raw+bytes([kind])+u(index)
    bodies=[b'\0\x20\0\x20\1\x3a\0\0\x0b',b'\0\x20\0\x40\0\x0b']
    return b'\0asm\1\0\0\0'+section(1,types)+section(3,b'\2\0\1')+section(5,b'\1\1\1\2')+section(7,exports)+section(10,b'\2'+b''.join(u(len(b))+b for b in bodies))
if __name__=='__main__':
    raw=module();(P/'probe.wasm').write_bytes(raw)
    print(json.dumps({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'sections':[1,3,5,7,10]}))
