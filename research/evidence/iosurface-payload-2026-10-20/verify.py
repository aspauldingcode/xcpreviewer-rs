"""Independent pinned-artifact metadata/instruction and owned fixture check."""
from pathlib import Path
import sys,json,hashlib,plistlib
root=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
from reloop.swiftmeta import MachO
with Controller().lock():
 base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');targets={}
 for name,pin in [('PreviewsMessagingHost','0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c'),('PreviewsDeveloperTools','d70f346fc8c8f7085f0a8b05fe160776b5464a3a6efc146259076fd12aa21cc2')]:
  p=base/(name+'.framework')/'Versions/A'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==pin;targets[name]=MachO(p)
 m=targets['PreviewsMessagingHost'];a=0xd6bc0;kind,size,n=m.unpack('<HHI',m.file_offset(a+8));assert (kind,size,n)==(2,12,5)
 keys=[m.string(m.relative(a+16+i*size+8)) for i in range(n)];assert keys==['surfaceID','scaleFactor','width','height','selectableRegions'];assert m.string(0xc6ca0)=='selectableRegions'
 m=targets['PreviewsDeveloperTools']
 for a,instruction in [(0x34538,0x1e600908),(0x34548,0x1e600929),(0x34590,0x6f00e402)]:assert m.unpack('<I',m.file_offset(a))[0]==instruction
 value={'surfaceID':12345,'scaleFactor':2.0,'width':1.5,'height':1.0,'selectableRegions':[{'path':'root/🪨','rect':{'x':1.0,'y':0.0,'width':2.0,'height':2.0},'serializedAccessibilityElement':b'\x00\xff'}]}
 f=root/'tools/re/rust/canvas-core/tests/fixtures/iosurface-payload';assert (f/'payload.bplist').read_bytes()==plistlib.dumps(value,fmt=plistlib.FMT_BINARY,sort_keys=True)
 assert (f/'generation2.bin').read_bytes()==bytes([0x19])*128
 print(json.dumps({'key_domain':keys,'pixel_dimension_fmul_instructions':2,'zero_corner_radius_instruction':True,'independent_payload_fixture_bytes_equal':True,'second_generation_bytes':128}))
