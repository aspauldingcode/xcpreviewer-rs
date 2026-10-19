"""Predeclared provider and competing full-buffer models; no measured constants."""
import struct
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
def norm(k):return f32(f32(k)*f32(1/255))
def decode(v):return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
def provider(route):
 b=bytearray(b'\xa5'*9408)
 for y in range(3):
  for x in range(768):
   a=255 if route==2 else x//3
   b[y*3136+x*4:y*3136+x*4+4]=bytes([128 if route==2 else a if c==x%3 else 0 for c in range(3)]+[a])
 return bytes(b)
def readback(route,candidate):
 b=bytearray(b'\xa5'*49152)
 for y in range(3):
  for x in range(768):
   a=1.0 if route==2 else norm(x//3)
   if route==2:v=[norm(128) if candidate=='identity' else f32(decode(norm(128)))]*3
   else:v=[(f32(decode(a)) if candidate=='transfer_premultiplied' else a) if c==x%3 else 0.0 for c in range(3)]
   b[y*12352+x*16:y*12352+x*16+16]=struct.pack('<4f',*v,a)
 return bytes(b)
