from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d' and m.uuid=='6b75229bde5d3d3794bc75af4f4704c6'
 a,b=0x2bc40,0x2c170;raw=Path(tempfile.mkdtemp(prefix='canvas-failure-policy-raw-',dir='/private/tmp'))
 out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/'policy.raw.s').write_bytes(out)
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
 assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
 def fields(base):
  k,z,c=struct.unpack('<HHI',m.read(base+8,8));assert z==12;names=[]
  for i in range(c):
   r=base+16+i*z;n=r+8+struct.unpack('<i',m.read(r+8,4))[0];buf=bytearray()
   for j in range(160):
    v=m.read(n+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('name bound')
   names.append(buf.decode())
  return names
 names=fields(0x1581a4);assert names==['test','log','softAssertDebugOnly','softAssert','fatalError'];w,e=struct.unpack('<II',m.read(0x150988+20,8));assert w&0xffffff==2 and e==3
 expected={0x2bd30:'LoggerV9logObject',0x2bd38:'errorABvgZ',0x2be28:'__os_log_impl',0x2bec8:'LoggerV9logObject',0x2bed0:'errorABvgZ',0x2bf38:'bridgeErrorToNSError',0x2bfcc:'__os_log_impl',0x2c078:'_assertionFailureBase',0x2c164:'_$ss17_assertionFailure__4file4line5flags'}
 calls=[]
 for pc,n in expected.items():
  t=m.resolve(m.branch(pc));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(n in x for x in ns),(hex(pc),t);calls.append({'call':hex(pc),'target':t})
 ops={0x2bcbc:0xa9405a9c,0x2bcc0:0x39404288,0x2bcc4:0x34000d48,0x2bcd4:0x7100051f,0x2bcd8:0x54000d01,0x2be70:0xd63f0380,0x2be78:0xaa160388,0x2be7c:0xb5000e08,0x2c03c:0xd2400388,0x2c040:0xaa160108,0x2c044:0xb5000568,0x2c07c:0x14000009,0x2c0bc:0xd65f03c0}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 # Evaluate only the decoded dispatch instructions for legal representations.
 def signed(x,n):return x-(1<<n) if x&(1<<(n-1)) else x
 def route(marker,low,high):
  pc=0x2bcc4;reg=marker;diff=None;visited=[];ends={0x2be6c,0x2bcdc,0x2be80,0x2c048,0x2c0f0}
  for _ in range(12):
   if pc in ends:return pc,visited
   visited.append(hex(pc));v=m.word(pc)
   if pc==0x2bcc4:pc=pc+4*signed((v>>5)&0x7ffff,19) if marker==0 else 0x2bcd4
   elif pc==0x2bcd4:diff=marker-1;pc+=4
   elif pc==0x2bcd8:pc=pc+4*signed((v>>5)&0x7ffff,19) if diff!=0 else pc+4
   elif pc==0x2be78:reg=low|high;pc+=4
   elif pc==0x2c03c:reg=low^1;pc+=4
   elif pc==0x2c040:reg|=high;pc+=4
   elif pc in (0x2be7c,0x2c044):pc=pc+4*signed((v>>5)&0x7ffff,19) if reg!=0 else pc+4
   else:raise AssertionError(hex(pc))
  raise AssertionError('dispatch bound')
 dispatch=[]
 for name,marker,low,high,entry in [('test',0,0x1000,0x2000,0x2be6c),('log',1,0,0,0x2bcdc),('softAssertDebugOnly',2,0,0,0x2be80),('softAssert',2,1,0,0x2c048),('fatalError',2,2,0,0x2c0f0)]:
  actual,visited=route(marker,low,high);assert actual==entry;dispatch.append({'case':name,'marker':marker,'payload_low':low,'payload_high':high,'entry':hex(actual),'visited':visited})
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'range':{'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()},'source_bytes_verified':b-a,'cases':names,'dispatch':dispatch,'calls':calls,'source_policy':{'test':'Invokes stored closure using its context, then reaches return epilogue if callback returns. Closure effects unqualified.','log':'Builds logger/callsite message and conditionally emits error-level os_log, with no assertion delegate on this branch. Effective logging controls remain unobserved.','softAssertDebugOnly':'In this pinned shipped image, branch builds error/callsite logging with NSError bridge and reaches cleanup/return. No _assertionFailureBase call on this source branch. Do not generalize across debug builds or versions.','softAssert':'Calls local _assertionFailureBase at 0x71290 then has return epilogue if delegate returns. Delegate internals and actual assertion/process behavior remain unqualified.','fatalError':'Formats error description and calls Swift standard-library _assertionFailure returning Never. No runtime crash/assertion was triggered.','boundary':'All five legal source representations checked by bounded branch interpretation. This is source dispatch, not native execution, independent behavioral oracle or proof of policy delivery/final cleanup.'},'scope':{'static_only':True,'native_private_calls':0,'actual_assertion_or_failure_control':False,'full_canvas_parity':False},'limitations':['Prior UI/Ghidra failures not retried unchanged.','Previous constructor policy softAssert remains distinct from its unqualified local assertion delegate effects.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':b-a,'selected_calls':len(calls),'legal_policy_routes':len(dispatch)}))
