"""Frozen arithmetic candidates; never read measured pixels to construct them."""
import struct
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
def value(code,candidate):return f32(code/255.0) if candidate=='divide' else f32(f32(code)*f32(1/255.0))
def provider(route):
 stride=4160 if route else 1088;raw=bytearray(b'\xa5'*(stride*3))
 for y in range(3):
  for x in range(256):
   for c in range(4):
    code=255 if c==3 else (x+c*85)&255
    if route:raw[y*stride+x*16+c*4:y*stride+x*16+c*4+4]=struct.pack('<f',value(code,'divide'))
    else:raw[y*stride+x*4+c]=code
 return bytes(raw)
def readback(candidate):
 raw=bytearray(b'\xa5'*16384)
 for y in range(3):
  for x in range(256):
   raw[y*4160+x*16:y*4160+x*16+16]=struct.pack('<4f',*[value((x+c*85)&255,candidate) for c in range(3)],1)
 return bytes(raw)
