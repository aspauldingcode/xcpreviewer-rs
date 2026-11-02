from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d' and m.uuid=='6b75229bde5d3d3794bc75af4f4704c6'
 raw=Path(tempfile.mkdtemp(prefix='canvas-observer-removal-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0x305c8,0x30600,'overfulfill-cleanup'),(0x41f10,0x41fdc,'cancel-closure'),(0x428d0,0x428f8,'remove-forwarder'),(0xbeea8,0xbeecc,'waiting-forwarder'),(0xbeef0,0xbf014,'waiting-update'),(0xee75c,0xee834,'dictionary-remove'),(0xdb40,0xdb50,'optional-cleanup')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0x305e4:'FulfillmentFailureModeOWOe',0x305ec:'_swift_release',0x41f68:'_swift_beginAccess',0x41f70:'_swift_weakLoadStrong',0x41f8c:'_os_unfair_lock_lock',0x41fac:'_os_unfair_lock_unlock',0x41fb4:'_swift_release',0x428e8:'OrderedDictionaryV11removeValue',0x428f4:'ConcurrentInvalidationObserverBoxVSgWOe',0xbeec0:'updateWaiting',0xee790:'_swift_isUniquelyReferenced_nonNull_native',0xee7b4:'_delete2at',0xee800:'remove2at',0xee828:'NativeDictionaryV4copy',0xdb48:'_swift_release'}
 calls=[]
 for pc,name in expected.items():
  t=m.resolve(m.branch(pc));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in n for n in ns),(hex(pc),t);calls.append({'call':hex(pc),'target':t})
 assert m.branch(0x41f28)==0x41f2c
 ops={0x305d8:0xf9402000,0x305dc:0xf9402661,0x305e0:0x39414262,0x305e8:0xf9403260,0x41f10:0xb0000002,0x41f14:0x91234042,0x41f18:0xb00003e3,0x41f1c:0x913aa063,0x41f20:0xb0000004,0x41f24:0x9123f084,0x41f74:0xb4000280,0x41f78:0xf9401008,0x41f80:0xf9404d17,0x41fa4:0xd63f0280,0x41fc0:0xd63f0260,0xbef20:0x79408008,0xbef3c:0x53083d08,0xbef40:0x7100051f,0xbef44:0x54000121,0xbef60:0x52800028,0xbefd0:0xd63f02e0,0xbefd4:0x52800008,0xbefe8:0x3901077f,0xbefec:0x390022c8,0xee784:0x36000341,0xee79c:0x34000440,0xee7d4:0xeb15015f,0xee7e8:0xd4200020,0xee7ec:0xd2800016,0xee7f0:0xd2800017,0xdb40:0xb4000060,0xdb44:0xaa0103e0}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 # This callback forwards the inout storage pointer and captured Identifier.
 assert m.word(0x428e0)==0xf9400a80 and m.word(0x428e4)==0xaa0803f4
 # Bind legal state ordering and waiting-update outcome names independently.
 def names(base):
  k,size,count=struct.unpack('<HHI',m.read(base+8,8));assert size==12;out=[]
  for i in range(count):
   a=base+16+size*i;p=a+8+struct.unpack('<i',m.read(a+8,4))[0];s=bytearray()
   for j in range(160):
    b=m.read(p+j,1)
    if b==b'\0':break
    s+=b
   else:raise AssertionError('name bound')
   out.append(s.decode())
  return out
 metadata={'state':names(0x15812c),'waiting_update':names(0x158154),'storage':names(0x1586a4)}
 assert metadata=={'state':['waiting','fulfilled'],'waiting_update':['updated','alreadyFulfilled'],'storage':['observers','managedTokens']}
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'metadata':metadata,'calls':calls,'source_policy':{'cancel_closure':'Concurrent makeCancelationToken closure configures removeObserver callback and updateWaitingState helper. Acquire strong owner from weak storage; missing owner returns. Live owner loads handle state/lock, locks, delegates waiting update, unlocks, releases strong owner, then destroys update outcome.','waiting_gate':'fulfilled state returns alreadyFulfilled outcome (tag 1) without invoking mutation callback. waiting state invokes callback with local ObserverAndTokenStorage, commits updated storage, keeps waiting discriminator 0, and returns updated outcome (tag 0). No transition to fulfilled is introduced by this route.','remove':'Callback uses captured Identifier, delegates OrderedDictionary.removeValue(forKey:), then destroys returned optional observer box before returning to locked caller. Dictionary miss returns nil; hit ensures unique dictionary storage, extracts/deletes value and removes matching Identifier from ordered keys. Inconsistent key storage traps. Dictionary copy/delete/array-remove internals are delegated, not fully qualified here.','context_release':'Present optional observer box cleanup tail-releases its context; absent returns. This release occurs inside removal callback before outer unlock. Actual zero-reference deinit/reentry or resource effects remain unobserved.','overfulfill_cleanup':'OverfulfillHandle cleanup destroys stored failure-mode value and releases closure context reference. This small helper has no direct failure-policy invocation; released context effects and failure-mode destructor internals remain opaque.','boundary':'This source route detaches an observer while waiting; it does not establish actual token cancellation delivery, handle invalidation, race safety or final resource settlement. Creation/registration and real repeated cancel controls remain open.'},'scope':{'static_only':True,'native_private_calls':0,'actual_token_cancel_or_reentry_control':False,'full_canvas_parity':False},'limitations':['Exploratory optional cleanup and waiting-update ranges included adjacent functions; final ranges stop at appropriate boundaries.','Previous locked-screen/Accessibility and Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'native_controls':0}))
