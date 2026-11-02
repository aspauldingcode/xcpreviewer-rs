from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d' and m.uuid=='6b75229bde5d3d3794bc75af4f4704c6'
 raw=Path(tempfile.mkdtemp(prefix='canvas-invalidation-fulfill-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0x30be0,0x30e60,'storage-fulfill'),(0xc12c0,0xc12f0,'trace-forwarder'),(0xbf9d0,0xbfaec,'trace-builder'),(0x30a1c,0x30b9c,'token-fulfill'),(0x1e5c,0x1e60,'empty-callback'),(0xbf75c,0xbf9d0,'caller')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 def field_names(base):
  kind,size,count=struct.unpack('<HHI',m.read(base+8,8));assert size==12;names=[]
  for i in range(count):
   r=base+16+size*i;n=r+8+struct.unpack('<i',m.read(r+8,4))[0];buf=bytearray()
   for j in range(200):
    v=m.read(n+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('field name bound')
   names.append(buf.decode())
  return names
 metadata={'state':field_names(0x15812c),'outcome':field_names(0x15817c),'storage':field_names(0x1586a4)}
 assert metadata=={'state':['waiting','fulfilled'],'outcome':['fulfilled','wasAlreadyFulfilled'],'storage':['observers','managedTokens']}
 for a,payload,empty in [(0x1508f8,2,0),(0x150958,1,1)]:
  w,e=struct.unpack('<II',m.read(a+20,8));assert w&0xffffff==payload and e==empty
 expected={0x30c14:'FulfillOnceStateC7fulfill',0xc12e4:'InvalidationHandleProtocolPAAE11_invalidate',0xbfa4c:'InvalidationTraceV4LinkO',0xbfac8:'append10contentsOf',0x30d8c:'OverfulfillHandleVWOh',0x30b34:'OverfulfillHandleVWOh',0xbf7d4:'FulfillOnceStateC7fulfill',0xbf7dc:'_os_unfair_lock_unlock',0xbf968:'FulfillOnceStateC7fulfill',0xbf970:'_os_unfair_lock_unlock'}
 calls=[]
 for pc,name in expected.items():
  t=m.resolve(m.branch(pc));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in n for n in ns),(hex(pc),t);calls.append({'call':hex(pc),'target':t})
 def branch(pc,condition):
  v=m.word(pc);assert v&0xff000010==0x54000000 and v&15==condition;d=(v>>5)&0x7ffff;d=d-(1<<19) if d&(1<<18) else d;return pc+4*d
 assert branch(0x30c88,1)==0x30da4 and branch(0x30a54,1)==0x30b4c and branch(0xbf97c,0)==0xbf8bc
 assert m.branch(0xc12c0)==0xc12c4
 ops={0x1e5c:0xd65f03c0,0xbf7a8:0xd0000001,0xbf7ac:0x910b0021,0xbf7b0:0xd0fffa05,0xbf7b4:0x913970a5,0xbf95c:0xb0fffb85,0xbf960:0x912800a5,0x30c64:0x79408008,0x30c80:0x53083d08,0x30c84:0x7100051f,0x30d78:0xd63f0100,0x30d94:0xb5000573,0x30d98:0x6f00e400,0x30d9c:0xad0002c0,0x30df0:0xf90002d3,0x30df8:0xfd0006c0,0x30dfc:0xf9000ad8,0x30e00:0x910062c8,0x30e08:0xd63f0380,0x30e0c:0xf9400ec0,0x30e10:0xf9000360,0x30e30:0x52800028,0x30e34:0x39010768,0x30a4c:0x3940e408,0x30a50:0x7100051f,0x30b28:0xd63f02e0,0x30b38:0xb5000213,0x30b3c:0x52800028,0x30b44:0x39000128,0x30b50:0xd63f0020,0x30b6c:0x52800028,0x30b70:0x3900e728,0x30b74:0x390002df,0xbf7ec:0xb4000db3,0xbf860:0xd63f02e0,0xbf974:0x3940e3e8,0xbf978:0x7100051f,0xbf980:0xd63f02e0,0xbfad0:0xf9000268}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 # Only legal state tags and normally returning callbacks are represented.
 matrix=[{'state':'waiting','storage_returned':True,'next_state':'fulfilled','observer_dispatch_enabled':True,'token_outcome':0,'token_callback_enabled':True},{'state':'fulfilled','storage_returned':False,'next_state':'fulfilled','observer_dispatch_enabled':False,'token_outcome':1,'token_callback_enabled':False}]
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'metadata':metadata,'calls':calls,'normal_return_source_matrix':matrix,'source_policy':{'storage_waiting':'Common helper copies waiting storage to outcome prefix, calls makeFulfilledState with output at +0x18, then installs returned trace and callsite into state and writes fulfilled discriminator 1 at +0x41. Prior waiting storage is returned for downstream dispatch. Callback/trace internals are only partially qualified.','storage_fulfilled':'Branch invokes configured ifAlreadyFulfilled callback and destroys OverfulfillHandle context. On normal no-error return, zeroes the 32-byte outcome, leaving no storage for caller dispatch. Callback throwing/error and OverfulfillHandle cleanup effects are not qualified here.','caller':'Concurrent invalidate passes trace builder through c12c0 and empty callback at 1e5c for already-fulfilled handling. Caller tests returned storage pointer after unlocking and skips both collection loops when absent.','trace':'Forwarder reaches trace builder, which constructs/appends InvalidationTrace.Link values and returns trace storage. It does not itself extract observer collections; the common fulfill helper copies waiting storage. Full link contents/ownership are not mapped.','managed_token':'Void/Void specialization compares state tag at +0x39. Waiting calls makeFulfilledState, installs callsite/tag 1 and writes outcome 0. Fulfilled invokes configured handler, cleans context and on normal no-error return writes outcome 1. Outer caller skips callback for outcome 1, otherwise invokes after unlock.','boundary':'One-shot dispatch suppression is source-qualified for legal tags and normal callback return. No actual repeated native invalidation, concurrency race/reentry, callback delivery, failure-policy behavior or final resource settlement observed.'},'scope':{'static_only':True,'native_private_calls':0,'actual_repeated_invalidation_control':False,'full_canvas_parity':False},'limitations':['No unchanged locked-screen/Accessibility or Ghidra failure retry.','Source matrix summarizes checked branches; it is not native runtime execution or an independent behavioral oracle.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'normal_return_cases':len(matrix)}))
