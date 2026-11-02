from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d' and m.uuid=='6b75229bde5d3d3794bc75af4f4704c6'
 raw=Path(tempfile.mkdtemp(prefix='canvas-token-destroy-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0x12a0ac,0x12a0ec,'token-destroy'),(0x2d00c,0x2d030,'mode-destroy'),(0x2ffa0,0x2ffb8,'mode-tag'),(0x1298ec,0x129904,'constructor-mode')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 def fields(base):
  k,size,count=struct.unpack('<HHI',m.read(base+8,8));assert size==12;out=[]
  for i in range(count):
   a=base+16+i*size;n=a+8+struct.unpack('<i',m.read(a+8,4))[0];buf=bytearray()
   for j in range(160):
    v=m.read(n+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('field name bound')
   out.append(buf.decode())
  return out
 metadata={'token':fields(0x15b70c),'failure_mode':fields(0x1581a4)}
 assert metadata=={'token':['callback','onceGuarantee'],'failure_mode':['test','log','softAssertDebugOnly','softAssert','fatalError']}
 w,empty=struct.unpack('<II',m.read(0x150988+20,8));assert w&0xffffff==2 and empty==3
 # Empty enum cases use marker 2 plus payload ordinal, not marker alone.
 tag_words=[0xb9400008,0x39404009,0x11000908,0x7100053f,0x1a898100,0xd65f03c0]
 for i,v in enumerate(tag_words):assert m.word(0x2ffa0+4*i)==v
 constant=m.read(0x132920,16);assert constant==struct.pack('<QQ',1,0)
 assert m.word(0x1298f0)==0xb0000048 and m.word(0x1298f4)==0x3dc24900 and m.word(0x1298f8)==0x3d801aa0 and m.word(0x1298fc)==0x52800048 and m.word(0x129900)==0x3901c2a8
 assert struct.unpack('<Q',m.read(0x1340e8,8))[0]==0x60 and any('failureMode' in n for n in m.named[0x1340e8])
 marker=2;payload=struct.unpack('<I',constant[:4])[0];tag=marker if marker<=1 else (payload+2)&0xffffffff;assert tag==3 and metadata['failure_mode'][tag]=='softAssert'
 expected={0x12a0e8:'_swift_release',0x2d020:'_swift_release',0x2d028:'_swift_bridgeObjectRelease'};calls=[]
 for pc,name in expected.items():
  t=m.resolve(m.branch(pc));assert t['kind']=='import_stub' and t['name']==name;calls.append({'call':hex(pc),'target':t})
 ops={0x12a0bc:0xf9400821,0x12a0c0:0xf85f8034,0x12a0c4:0xf9400688,0x12a0c8:0xd63f0100,0x12a0cc:0xf9402288,0x12a0d0:0x8b080268,0x12a0d4:0x91001d08,0x12a0d8:0x927df108,0x12a0dc:0xf9400100,0x2d00c:0x12001c48,0x2d010:0x7100051f,0x2d014:0x54000080,0x2d018:0x350000a8,0x2d02c:0xd65f03c0}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 assert [pc for pc in range(0x12a0ac,0x12a0ec,4) if m.word(pc)>>26 in (5,37)]==[0x12a0e8]
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'metadata':metadata,'constructor_failure_policy':{'constant_address':'0x132920','constant_bytes':16,'constant_sha256':hashlib.sha256(constant).hexdigest(),'marker':marker,'payload_ordinal':payload,'logical_tag':tag,'case':'softAssert','native_tag_accessor':'0x2ffa0'},'calls':calls,'source_policy':{'token_destroy':'Destroy callback through its generic type witness, advance by callback size rounded to 8-byte alignment, load following onceGuarantee reference and tail-call swift_release. Complete body contains no explicit cancel call; dynamic callback destructor and released guarantee effects remain opaque.','failure_policy':'Concrete ConcurrentTokenCallback token constructor stores failureMode at state-owner offset +0x60: constant payload ordinal 1 and marker 2. Native tag accessor returns payload+2 for marker >1, hence logical tag 3 softAssert. Marker 2 alone does not identify softAssertDebugOnly.','mode_destroy':'Representation marker 0 releases closure context, marker 1 bridge-releases storage, other markers return. The constructor-selected empty case therefore has no payload reference release in this helper. No runtime assertion policy or severity inferred beyond named case selection.','boundaries':'Previously recovered FulfillOnceState deinit can invoke configured policy while waiting, but this unit does not prove last ownership, actual deinit, cancellation, assertion delivery, process behavior or final resource settlement. No claim that token destruction cannot cancel through delegated effects.'},'scope':{'static_only':True,'native_private_calls':0,'actual_token_destroy_or_assertion_control':False,'full_canvas_parity':False},'limitations':['Initial exploratory tag-witness range was a prefix; final range includes select and return before naming constructor policy. No claim based on marker alone.','Previous locked-screen/Accessibility and Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'constructor_policy':metadata['failure_mode'][tag]}))
