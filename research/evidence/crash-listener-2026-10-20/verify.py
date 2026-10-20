"""Independent artifact metadata and original Python fixture-byte verification."""
from pathlib import Path
import sys,json,hashlib,plistlib
root=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
from reloop.swiftmeta import MachO
with Controller().lock():
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost')
 assert hashlib.sha256(p.read_bytes()).hexdigest()=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c'
 m=MachO(p);observed={}
 domains={0xd429c:['discriminant','payload'],0xd42c4:['startListeningIfNeeded','nextCrashReport'],0xd42ec:['process','timeout'],0xd4314:['crashReport'],0xd4330:['discriminant','payload'],0xd4358:['pid','processName']}
 for address,expected in domains.items():
  kind,size,n=m.unpack('<HHI',m.file_offset(address+8));assert kind==2 and size==12 and n==len(expected)
  names=[m.string(m.relative(address+16+i*size+8)) for i in range(n)];assert names==expected;observed[hex(address)]=names
 assert m.string(0xc4f40)=='startListeningIfNeeded'
 fixtures=root/'tools/re/rust/canvas-core/tests/fixtures/crash-listener'
 values={'pid-message':{'discriminant':'nextCrashReport','payload':{'process':{'discriminant':'pid','payload':12345},'timeout':3.5}},'name-message':{'discriminant':'nextCrashReport','payload':{'process':{'discriminant':'processName','payload':'Preview 🪨'},'timeout':-0.0}},'start-message':{'discriminant':'startListeningIfNeeded'}}
 report=root/'tools/re/rust/canvas-core/tests/fixtures/crash-report-model/report-canonical.bplist'
 values['response']={'crashReport':plistlib.loads(report.read_bytes())}
 for name,v in values.items():assert (fixtures/(name+'.bplist')).read_bytes()==plistlib.dumps(v,fmt=plistlib.FMT_BINARY,sort_keys=True)
 print(json.dumps({'metadata_domains':observed,'independent_fixture_bytes_equal':len(values),'report_fixture_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'private_native_calls':0}))
