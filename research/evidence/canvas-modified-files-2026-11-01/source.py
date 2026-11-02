from pathlib import Path
import fcntl,hashlib,json,re,subprocess,tempfile,struct
from macho import Image
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;p=Path('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode')
with (r/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=Image(p);digest=hashlib.sha256(m.data).hexdigest();assert digest=='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b' and m.uuid=='25c99c664185307188e31ab474573a10'
 rawdir=Path(tempfile.mkdtemp(prefix='canvas-modified-files-raw-',dir='/private/tmp'));ranges=[]
 for a,b,n in [(0x24e3d4,0x24e808,'filter'),(0x250314,0x250a48,'should-update')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(rawdir/(n+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':n,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0x24e720:'shouldUpdateModifiedFile',0x2503b0:'isOpenAndThunkable',0x250504:'_objc_msgSend$conformsTo:',0x250540:'_objc_msgSend$conformsTo:',0x25057c:'_objc_msgSend$conformsTo:',0x2505b4:'_objc_msgSend$conformsTo:',0x2507ec:'_objc_msgSend$pathComponents',0x250830:'lowercased',0x250858:'_stringCompareWithSmolCheck',0x250890:'_objc_msgSend$pathExtension',0x2508dc:'_stringCompareWithSmolCheck'}
 calls=[]
 for a,part in expected.items():
  t=m.resolve(m.branch(a));names=[t['name']] if t['kind']=='import_stub' else t['names']
  if part=='shouldUpdateModifiedFile':assert m.branch(a)==0x250314
  elif part=='isOpenAndThunkable':assert m.branch(a)==0x250a48 and any('isOpenAndThunkable' in n for n in names)
  else:assert any(part in n for n in names),(hex(a),names)
  calls.append({'call':hex(a),'target':t})
 ops={0x24e4d0:0xb5000a37,0x24e724:0x37000160,0x2503b4:0x36000920,0x250514:0x370005b8,0x250550:0x370003d8,0x25058c:0x370001f8,0x2505c4:0x36001098,0x2507b0:0x52800000,0x2508ec:0x370000f4,0x2508f0:0x52800020,0x2508f4:0x17ffffb0}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 # Read the short ASCII comparison constants from MOVZ/MOVK sequences.
 def short_constant(a):
  v=m.word(a);assert v&0xff80001f==0xd2800014;value=((v>>5)&65535)<<(((v>>21)&3)*16)
  for pc in range(a+4,a+16,4):
   v=m.word(pc);assert v&0xff80001f==0xf2800014
   shift=((v>>21)&3)*16;value=(value&~(65535<<shift))|(((v>>5)&65535)<<shift)
  return value.to_bytes(8,'little').rstrip(b'\0').decode()
 assert short_constant(0x2507d8)=='.swiftpm';assert short_constant(0x250874)=='swiftpm'
 types=[]
 for a,s in [(0x2d8f50,'com.apple.application-bundle'),(0x2d8f70,'com.apple.pluginkit'),(0x2d8f90,'com.apple.framework'),(0x2d8fb0,'com.apple.dt.swiftpm-user-managed-folder')]:assert m.read(a,len(s)+1)==s.encode()+b'\0';types.append({'address':hex(a),'type':s})
 assert any('filterfg3ForH0' in n for n in m.named[0x24e3d4])
 result={'image':{'path':str(p),'sha256':digest,'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'calls':calls,'excluded_conforming_types':types,'source_policy':{'missing_data_type':'Skip entry; no type inference performed in this function.','predicate_true':'Keep typed entry.','open_thunkable':'If isOpenAndThunkable(path) returns true, shouldUpdateModifiedFile returns false. Helper internals not qualified by this unit.','excluded_types':'Conformance to any recovered bundle/package type returns false.','path_component':'A path component lowercased equal to .swiftpm returns false.','path_extension':'Extension equal to swiftpm returns false; no lowercasing of extension on inspected path.','remaining_typed_files':'Return true after these exclusions.'},'scope':{'static_only':True,'private_native_calls':0,'native_file_change_delivery_observed':False,'fresh_ui_observation':False,'isOpenAndThunkable_internals_recovered':False,'handler_followup_effects_complete':False,'full_canvas_parity':False,'exploratory_range_correction':'Initial filter exploration ended at next makeBuilder (0x24e884), including adjacent editor-settings key-path setter. Final verified filter range ends at actual next symbol 0x24e808.'}}
 (w/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls_bound':len(calls),'excluded_types':len(types)}))
