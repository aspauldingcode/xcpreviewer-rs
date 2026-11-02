from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsScenes.framework/Versions/A/PreviewsScenes');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09' and m.uuid=='afaf513ac1153755840e1d82b40e7d93'
 raw=Path(tempfile.mkdtemp(prefix='canvas-pinning-didset-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0x58e98,0x5930c,'didset'),(0x5930c,0x593f8,'change'),(0x625b4,0x625d0,'event-tag')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0x58f68:'PreviewFileVMa',0x590a8:'PreviewFileV18previewDescriptionxvg',0x5912c:'PreviewFileV18previewDescriptionxvg',0x592b8:'_$sSQ2eeoiySbx_xtFZTj',0x59264:'pinnedFileDidChange',0x59330:'PreviewUpdateReasonVMa',0x59370:'PreviewUpdateReasonV15previewsChangedACvgZ',0x59378:'PreviewServiceC14setNeedsUpdate',0x593b4:'EventStreamV4SinkC4sendyyxF',0x593dc:'previewablesDidChange'}
 calls=[]
 for a,name in expected.items():
  t=m.resolve(m.branch(a));names=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in s for s in names),(hex(a),t);calls.append({'call':hex(a),'target':t})
 def fields(base):
  kind,size,count=struct.unpack('<HHI',m.read(base+8,8));assert size==12
  return [m.read(a+8+struct.unpack('<i',m.read(a+8,4))[0],120).split(b'\0',1)[0].decode() for a in [base+16+i*size for i in range(count)]]
 fs=fields(0x8c5a0);assert len(fs)==25 and fs[8]=='pinningState' and fs[12:14]==['eventsSink','previewService']
 assert struct.unpack('<II',m.read(0x8b91c+36,8))==(25,12)
 cases=fields(0x8c6dc);assert cases==['documentWasRenamed','displayableContentChanged','noCanvasContentSymbolsPresent','canvasContentSymbolsPresent','pinnedFileDidChange']
 assert struct.unpack('<II',m.read(0x8b978+20,8))==(2,3)
 ops={0x59040:0xf9405375,0x59094:0x7100041f,0x59098:0x54000100,0x59114:0x7100041f,0x5911c:0x54000100,0x591a8:0x7100041f,0x591ac:0x54000241,0x591dc:0x7100041f,0x591e0:0x54000361,0x591f0:0x1400001e,0x59218:0x7100041f,0x5921c:0x54000361,0x59304:0x3607faf3,0x59308:0x17ffffd8,0x59364:0xf94066e8,0x59390:0xf9406108,0x59398:0x52800048,0x5939c:0xf81a03a8,0x593ac:0x381c83a8,0x625b8:0x3940a000,0x625bc:0x7100081f,0x625c0:0x54000063,0x625c4:0xb9400108,0x625c8:0x11000900}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'calls':calls,'field_offsets':{'vector_word_offset':12,'pinningState_index':8,'eventsSink_index':12,'previewService_index':13,'metadata_slots':['0xa0','0xc0','0xc8']},'event_metadata':{'field_descriptor':'0x8c6dc','payload_cases':2,'empty_cases':3,'cases':cases,'emitted_empty_word':2,'emitted_tag_byte':2,'logical_event':cases[2+2]},'source_policy':{'comparison':'Project current and old pinningState.file to optional PreviewFile.previewDescription. Both absent returns; one absent calls pinnedFileDidChange; both present calls it only when generic Equatable equality is false.','sources_only':'Equal optional descriptions skip this callback; source-set changes alone are not tested by this didSet route.','downstream_order':['previewService.setNeedsUpdate(previewsChanged)','eventsSink.send(pinnedFileDidChange)','previewablesDidChange()'],'scope':'Source submission/call order only. Event consumers, previewablesDidChange effects, actual rebuild/render/state completion and resource settlement unqualified.'},'scope':{'static_only':True,'private_native_calls':0,'native_event_observed':False,'previewables_didchange_effects_qualified':False,'full_canvas_parity':False},'limitations':['Prior locked-screen/empty Accessibility observation not retried unchanged.','Source inspection and combined reader-writing escalations each hit permission-review timeout before execution; shorter separated execution used, without inferring unsafe-action rejection.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'event':cases[4]}))
