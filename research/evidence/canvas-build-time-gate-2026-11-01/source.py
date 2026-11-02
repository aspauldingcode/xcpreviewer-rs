from pathlib import Path
import fcntl,hashlib,json,re,subprocess,tempfile
from macho import Image
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;p=Path('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode')
with (r/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=Image(p);digest=hashlib.sha256(m.data).hexdigest();assert digest=='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b' and m.uuid=='25c99c664185307188e31ab474573a10'
 rawdir=Path(tempfile.mkdtemp(prefix='canvas-build-time-gate-raw-',dir='/private/tmp'));ranges=[]
 for a,b,n in [(0x2495e0,0x24965c,'timestamp-presence'),(0x24985c,0x249960,'build-start'),(0x249b8c,0x249bf4,'time-check'),(0x249e08,0x249ea4,'suppressed-cleanup'),(0x249960,0x2499c4,'build-start-pause'),(0x249df8,0x249e08,'return-branches'),(0x24a0c4,0x24a0d0,'cleanup-return')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(rawdir/(n+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':n,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0x249868:'_$s10Foundation4DateVACycfC',0x249bb0:'_$s10Foundation4DateVACycfC',0x249bc0:'_$s10Foundation4DateV17timeIntervalSinceySdACF',0x2498d4:'CoalescerC14setNeedsUpdateyyF',0x249910:'_$s16PreviewsPipeline19PreviewUpdateReasonV16workspaceChangedyACSSFZ',0x249944:'_$s14PreviewsScenes14WorkspaceSceneC14setNeedsUpdate3fory0A8Pipeline07PreviewG6ReasonV_tF'}
 calls=[]
 for a,name in expected.items():
  t=m.resolve(m.branch(a));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in n for n in ns),(hex(a),ns);calls.append({'call':hex(a),'target':t})
 # Bind the actual scene pause call and imported enum-case global.
 t=m.resolve(m.branch(0x2499a8));assert t['name']=='_$s14PreviewsScenes14WorkspaceSceneC5pause3fory0A8Pipeline18PreviewPauseReasonO_tF';calls.append({'call':'0x2499a8','target':t})
 a=0x337ad8;s=next(s for s in m.sections if s['vm']<=a<s['vm']+s['length']);assert s['flags']&255==6 and (a-s['vm'])%8==0
 reason=m.symbols[m.indirect[s['r1']+(a-s['vm'])//8]];assert reason=='_$s16PreviewsPipeline18PreviewPauseReasonO18userInitiatedBuildyA2CmFWC'
 assert any('lastBuildTimestamp' in n for n in m.named[0x36cc08])
 ops={0x2495e4:0xf9460513,0x249638:0x7100041f,0x24963c:0x54002a81,0x249658:0x14000167,0x249874:0x52800001,0x249878:0x52800022,0x249888:0xf9460513,0x2498b0:0x8b130321,0x2498c4:0x37003e3b,0x2498dc:0xf945a908,0x2498e4:0xf8286b3f,0x249bb8:0xaa1403f7,0x249bbc:0xaa1c03f4,0x249bc4:0x4ea01c08,0x249bd8:0x1e601000,0x249bdc:0x1e602100,0x249be0:0x5400114d,0x249df8:0x140000a4,0x249e94:0xf85003a1,0x249ea0:0x14000089}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 result={'image':{'path':str(p),'sha256':digest,'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'calls':calls,'pause_reason_import':reason,'source_policy':{'timestamp':'Build-start path constructs current Foundation.Date and writes present optional lastBuildTimestamp.','build_payload_flag':'After timestamp assignment, true low payload bit exits; false continues to coalescer scheduling, cached-builder clear, optional workspaceChanged scene update and pause(userInitiatedBuild). The payload bit meaning is not recovered here.','modified_files':'Missing timestamp proceeds to later external-change gate. Present timestamp compares Date().timeIntervalSince(lastBuildTimestamp) against native immediate 2.0; branch <=2 enters suppressed cleanup/return, otherwise continues to later gate.','boundary':'Exactly two seconds follows the suppression branch in source. No timer, scheduled retry, measured debounce interval or native timing experiment established.'},'scope':{'static_only':True,'private_native_calls':0,'fresh_ui_observation':False,'native_timestamp_or_event_timing_observed':False,'payload_flag_origin_known':False,'complete_refresh_behavior':False,'full_canvas_parity':False}}
 (w/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls_bound':len(calls),'comparison_seconds':2.0}))
