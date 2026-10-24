"""Offline pinned MessagingHost command-domain and branch verification."""
from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
w=Path(__file__).parent;result=json.loads((w/'findings.json').read_text());p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');m=MachO(p)
assert hashlib.sha256(m.data).hexdigest()==result['target_sha256'];assert m.uuid==result['uuid']
names=['previewInstances','incrementalPreviewInstances','render','incrementalRender','display','incrementalDisplay','layerHost','incrementalLayerHost','captureIOSurface','incrementalCaptureIOSurface']
a=0xd6070;assert m.unpack('<HHI',m.file_offset(a+8))==(2,12,10)
assert [m.string(m.relative(a+16+i*12+8)) for i in range(10)]==names
assert m.unpack('<10I',m.file_offset(0xbf4a4))==tuple(range(10))
branches=m.data[m.file_offset(0xbe560):m.file_offset(0xbe560)+10]
expected=[1,1,3,3,5,5,7,7,9,9]
for tag,delta in enumerate(branches):
    target=0x88608+delta*4
    if delta==0: assert tag%2==1;value=tag
    elif target==0x88664:value=1
    else:
        ins=m.u32(m.file_offset(target));assert ins&0xff80001f==0x52800008;value=(ins>>5)&65535
    assert value==expected[tag]
assert [m.u32(m.file_offset(0x88734+i*4)) for i in range(6)]==[0x39400288,0x7100211f,0x1a9f97e9,0x2a080128,0x12000100,0xd65f03c0]
assert [m.string(a) for a in [0xc5490,0xc54b0,0xc54d0,0xc54f0,0xc5510,0xc5530,0xc5550]]==[names[i] for i in [9,8,7,5,3,1,0]]
prefix=[0xbe560,0xbe56a];assert list(m.data[m.file_offset(prefix[1]):m.file_offset(prefix[1])+10])==[0,14,22,23,5,39,47,31,54,11]
s=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address=0x88594','--stop-address=0x888e0',str(p)],capture_output=True,timeout=20,check=True).stdout.decode()
words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',s,re.M)}
for body in result['bodies']:
    a=int(body['start'],16);n=body['bytes'];raw=m.data[m.file_offset(a):m.file_offset(a)+n]
    assert hashlib.sha256(raw).hexdigest()==body['sha256'];assert b''.join(words[x] for x in range(a,a+n,4))==raw
print(json.dumps({'cases':10,'incremental_pairs':5,'selected_body_bytes_verified':sum(b['bytes'] for b in result['bodies']),'source_only':True}))
