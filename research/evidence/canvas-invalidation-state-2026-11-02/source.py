from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d' and m.uuid=='6b75229bde5d3d3794bc75af4f4704c6'
 raw=Path(tempfile.mkdtemp(prefix='canvas-invalidation-state-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0x41df0,0x41f10,'handle-initializer'),(0x41fdc,0x4202c,'handle-deinit'),(0x2b980,0x2bc40,'state-deinit'),(0xbf75c,0xbf9d0,'explicit-invalidate'),(0xbfcc8,0xbfd10,'invalidate-witness')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 def fields(base):
  kind,size,count=struct.unpack('<HHI',m.read(base+8,8));assert size==12;names=[]
  for i in range(count):
   r=base+16+i*size;n=r+8+struct.unpack('<i',m.read(r+8,4))[0];buf=bytearray()
   for j in range(200):
    v=m.read(n+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('name bound')
   names.append(buf.decode())
  return names
 metadata={'handle':fields(0x158638),'state_owner':fields(0x1580d4),'state_cases':fields(0x15812c),'storage':fields(0x1586a4)}
 assert metadata=={'handle':['name','state'],'state_owner':['initializationCallsite','initializationInfo','failureMode','thing','action','state'],'state_cases':['waiting','fulfilled'],'storage':['observers','managedTokens']}
 word,empty=struct.unpack('<II',m.read(0x1508f8+20,8));assert word&0xffffff==2 and empty==0
 offsets=[]
 for a,offset,fragment in [(0x1340e0,0x50,'initializationInfo'),(0x1340e8,0x60,'failureMode'),(0x134100,0x98,'OSAllocatedUnfairLock'),(0x1353c8,0x20,'ConcurrentInvalidationHandleC5state')]:
  assert struct.unpack('<Q',m.read(a,8))[0]==offset;names=m.named[a];assert any(fragment in n for n in names);offsets.append({'address':hex(a),'offset':hex(offset),'symbols':names})
 # The exact native field-offset symbol encodes the concrete handle state type.
 concrete=m.named[0x1353c8][0]
 assert 'FulfillOnceStateCyAA23ObserverAndTokenStorageVyAA0deK3BoxVAA0dM8CallbackVGAA0E5TraceVG' in concrete
 expected={0x41e2c:'OrderedDictionaryV17dictionaryLiteral',0x41ff0:'_swift_release',0x2ba5c:'4peek8callsite',0x2ba68:'_swift_getEnumCaseMultiPayload',0x2bb5c:'Unfulfilled',0x2bb84:'_swift_allocError',0x2bbd8:'FulfillmentFailureModeO4fail',0x2bbec:'_swift_errorRelease',0x2bc18:'_swift_release',0xbfcfc:'InvalidationHandleProtocolPAAE11_invalidate',0xbf79c:'_swift_retain',0xbf7a4:'_os_unfair_lock_lock',0xbf7d4:'FulfillOnceStateC7fulfill',0xbf7dc:'_os_unfair_lock_unlock',0xbf7e4:'_swift_release',0xbf858:'_swift_retain',0xbf868:'_swift_release',0xbf93c:'_os_unfair_lock_lock',0xbf968:'FulfillOnceStateC7fulfill',0xbf970:'_os_unfair_lock_unlock'}
 calls=[]
 for pc,name in expected.items():
  t=m.resolve(m.branch(pc));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in n for n in ns),(hex(pc),t);calls.append({'call':hex(pc),'target':t})
 ops={0x41eec:0xf9001296,0x41fec:0xf9401280,0x2b9e8:0xf9404e88,0x2ba6c:0x7100041f,0x2ba70:0x540000c1,0x2ba80:0xd63f0100,0x2bac8:0xf9402a7a,0x2bacc:0xb400023a,0x2baf4:0xd63f0340,0xbf784:0xf9401294,0xbf794:0xf9404e96,0xbf7ec:0xb4000db3,0xbf860:0xd63f02e0,0xbf924:0xf9404f56,0xbf974:0x3940e3e8,0xbf978:0x7100051f,0xbf97c:0x54fffa00,0xbf980:0xd63f02e0}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 assert m.branch(0x2ba84)==0x2bbf0
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'metadata':metadata,'field_offsets':offsets,'calls':calls,'source_policy':{'ownership':'Concurrent handle state field at +0x20 is FulfillOnceState<ObserverAndTokenStorage<ConcurrentInvalidationObserverBox,InvalidationTokenCallback>,InvalidationTrace>. Initializer stores state reference; handle deinit releases it. State owner contains OSAllocatedUnfairLock-backed state at +0x98. Reference release does not prove state deinit runs.','state_deinit':'Peek lock-backed state and inspect waiting/fulfilled tag. fulfilled (tag 1) destroys snapshot and skips unfulfilled failure construction. waiting destroys waiting snapshot, evaluates optional initializationInfo closure when present, builds Unfulfilled error and calls configured FulfillmentFailureMode.fail, then releases own fields. Failure policy internals and concrete configured mode are not qualified here; no direct observer invalidation call is established here, while initializationInfo effects remain opaque.','explicit_invalidate':'Protocol witness forwards to concurrent invalidate specialization. Retain state, lock, call specialized fulfill closure, unlock, release state, then inspect extracted observer/token storage. Nonempty first collection dispatches observer closure pairs after unlock. Second managed-token loop takes each token state lock, calls another fulfill specialization, unlocks, and skips its callback when returned discriminator equals 1; otherwise invokes callback. Internal fulfill transition semantics and callback contents remain unqualified.','boundaries':'Source distinguishes explicit invalidation dispatch from last-owner unfulfilled diagnostics. No actual callback, zero reference count, cancellation timing, deadlock/reentry behavior or final resource settlement observed.'},'scope':{'static_only':True,'native_private_calls':0,'actual_lifetime_or_cancellation_control':False,'full_canvas_parity':False},'limitations':['Exploratory disassembly ranges included adjacent function bodies. Final qualification ranges stop at deinit and specialization boundaries; adjacent failure-policy implementation is excluded.','Previous locked-screen/Accessibility and Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'native_controls':0}))
