from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d' and m.uuid=='6b75229bde5d3d3794bc75af4f4704c6'
 raw=Path(tempfile.mkdtemp(prefix='canvas-observer-registration-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0xbf014,0xbf178,'registration'),(0xc1218,0xc12c0,'insert'),(0x129858,0x1299f4,'token-create-cancel'),(0x129a64,0x129a84,'token-invoke'),(0xc12f0,0xc1300,'forwarders'),(0xbeef0,0xbf014,'waiting-update'),(0x30a1c,0x30b9c,'token-fulfill')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0xbf050:'_os_unfair_lock_lock',0xbf07c:'updateWaiting',0xbf084:'_os_unfair_lock_unlock',0xbf0e4:'_swift_allocObject',0xbf0f4:'_swift_weakInit',0xbf108:'_swift_allocObject',0xbf15c:'CancelationTokenV8callsite8callback',0xc1254:'_os_unfair_lock_lock',0xc1268:'_os_unfair_lock_unlock',0xc1280:'OrderedDictionaryV11updateValue',0xc1284:'ConcurrentInvalidationObserverBoxVSgWOe',0xc12b8:'_swift_once',0x1298a0:'_swift_allocObject',0x1298c4:'_swift_allocObject',0x12997c:'_os_unfair_lock_lock',0x1299ac:'FulfillOnceStateC7fulfill',0x1299b4:'_os_unfair_lock_unlock'}
 calls=[]
 for pc,name in expected.items():
  t=m.resolve(m.branch(pc));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in n for n in ns),(hex(pc),t);calls.append({'call':hex(pc),'target':t})
 assert m.branch(0xc12f4)==0xc1218 and m.branch(0xc12fc)==0x41f10
 ops={0xbf054:0xd0000001,0xbf058:0x910bc021,0xbf08c:0x394063e8,0xbf090:0x7100051f,0xbf094:0x54000201,0xbf0ac:0xd63f02c0,0xbf0c8:0xa9007e7f,0xbf0cc:0xf9000a7f,0xbf0f0:0xaa1403e1,0xbf110:0xa9015416,0xbf14c:0xd0000001,0xbf150:0x910be021,0xc1258:0xf9400b17,0xc125c:0x910006e8,0xc1260:0xf9000b08,0xc1290:0xf9000277,0x129870:0xa9000901,0x1298c8:0xb9004c1f,0x1298cc:0x3901241f,0x1298d0:0xf9004ea0,0x129928:0xf9000a75,0x1299b8:0x39403fe8,0x1299bc:0x7100051f,0x1299c0:0x540000c1,0x1299d4:0xd65f03c0,0x1299dc:0xf9400422,0x1299f0:0xd61f0040,0x129a70:0xa9405288,0x129a74:0xd63f0100,0xbef40:0x7100051f,0xbef44:0x54000121,0xbef60:0x52800028,0xbefd0:0xd63f02e0,0xbefd4:0x52800008,0xbefe8:0x3901077f,0x30a50:0x7100051f,0x30a54:0x540007c1,0x30b3c:0x52800028,0x30b44:0x39000128,0x30b70:0x3900e728,0x30b74:0x390002df}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 def fields(base):
  k,size,count=struct.unpack('<HHI',m.read(base+8,8));assert size==12;out=[]
  for i in range(count):
   a=base+16+i*size;n=a+8+struct.unpack('<i',m.read(a+8,4))[0];buf=bytearray()
   for j in range(160):
    v=m.read(n+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('name bound')
   out.append(buf.decode())
  return out
 metadata={'token':fields(0x15b70c),'concurrent_callback':fields(0x15b75c),'state':fields(0x15812c),'waiting_update':fields(0x158154),'outcome':fields(0x15817c)}
 assert metadata=={'token':['callback','onceGuarantee'],'concurrent_callback':['didCancel'],'state':['waiting','fulfilled'],'waiting_update':['updated','alreadyFulfilled'],'outcome':['fulfilled','wasAlreadyFulfilled']}
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'metadata':metadata,'calls':calls,'source_policy':{'registration':'Lock handle state and update only waiting storage, then unlock before inspecting outcome. Already fulfilled invokes supplied observer with existing trace after unlock and returns absent optional token. Waiting invokes insertion helper and creates a cancellation token. Normal return only; no actual callback delivery observed.','insertion':'Lazy-initialize counter storage through swift_once if needed. Under a separate counter lock, load prior counter value and increment/store; use prior value as Identifier for OrderedDictionary.updateValue, clean replaced optional observer and return Identifier. No wraparound, cross-process namespace or allocation-failure guarantee inferred; dictionary update internals remain delegated.','weak_token':'Waiting-registration branch allocates a weak owner box with swift_weakInit(handle), then closure context holding weak box and observer Identifier. Token callback forwarder loads these and reaches previously qualified removal closure at 0x41f10. This weak edge does not rule out other reference cycles in user callbacks.','token_construction':'Concrete constructor stores callback pair and a onceGuarantee reference. Allocated backing lock/state storage is initialized; complete failure-mode policy/type layout not mapped here.','token_cancel':'Locks onceGuarantee state, calls Void/Void fulfill specialization, unlocks, returns without invoking callback when outcome is 1. Otherwise tail-delegates protocol callback invoke; concrete ConcurrentTokenCallback invokes its closure pair. Included helper bytes bind initial waiting outcome 0 versus normally returning already-fulfilled outcome 1. Throws/failure-context effects remain unqualified.','boundaries':'Source qualifies late-observer invocation, waiting registration, weak removal capture and one-shot cancel gate. It does not prove actual registration/cancel delivery, token deinit auto-cancellation, weak-owner-loss behavior, races/reentry or final resource settlement.'},'scope':{'static_only':True,'native_private_calls':0,'actual_registration_or_cancel_control':False,'full_canvas_parity':False},'limitations':['Exploratory forwarding range included adjacent unnamed trampolines; final range excludes them.','Previous locked-screen/Accessibility and Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'native_controls':0}))
