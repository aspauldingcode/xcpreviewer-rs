"""Emit a research scalar arithmetic probe; no imports, memory, start or renderer."""
from pathlib import Path
import struct,hashlib,json
P=Path(__file__).resolve().parent
def u(n):
 out=bytearray()
 while True:
  b=n&127;n>>=7;out.append(b|(128 if n else 0))
  if not n:return bytes(out)
def section(kind,raw):return bytes([kind])+u(len(raw))+raw
def module():
 names=['multiplyBits','divideBits'];exports=b'\2'
 for i,name in enumerate(names):raw=name.encode();exports+=u(len(raw))+raw+b'\0'+u(i)
 bodies=[]
 for constant,opcode in [(1/255,0x94),(255,0x95)]:
  body=b'\0\x20\0\xb3\x43'+struct.pack('<f',constant)+bytes([opcode,0xbc,0x0b]);bodies.append(u(len(body))+body)
 return b'\0asm\1\0\0\0'+section(1,b'\1\x60\1\x7f\1\x7f')+section(3,b'\2\0\0')+section(7,exports)+section(10,b'\2'+b''.join(bodies))
if __name__=='__main__':
 raw=module();(P/'probe.wasm').write_bytes(raw);print(json.dumps({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'sections':[1,3,7,10]}))
