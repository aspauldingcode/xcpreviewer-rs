from pathlib import Path
import fcntl,hashlib,json,re,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
root=Path('/Users/8amps/xcpreviewer-rs')
rawdir=Path(tempfile.mkdtemp(prefix='canvas-build-listener-raw-',dir='/private/tmp'))
with (root/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 images={}
 for name,digest,uuid in [('PreviewsXcode','ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b','25c99c664185307188e31ab474573a10'),('PreviewsIDEAPI','d3e0ad14a4ea159fde12482d92fb7b7d3f86e4df1578fcef76961a294fbe71f0','b8c195f9db4837999653d7aa8bcb986e')]:
  p=Path('/Applications/Xcode.app/Contents/PlugIns')/(name+'.framework/Versions/A')/name
  m=Image(p);assert hashlib.sha256(m.data).hexdigest()==digest and m.uuid==uuid
  images[name]=m
 ranges=[]
 for name,a,b,label in [('PreviewsXcode',0x16c734,0x16c8ac,'registrations'),('PreviewsXcode',0x16ed0c,0x16ef1c,'start-callback'),('PreviewsXcode',0x16ef1c,0x16f130,'stop-callback'),('PreviewsXcode',0x16f424,0x16f434,'callback-forwarders'),('PreviewsXcode',0x16f5a0,0x16f5a4,'subscriber-forwarder'),('PreviewsIDEAPI',0x8fb0,0x8fd0,'preview-build-classifier')]:
  m=images[name]
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout
  (rawdir/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'image':name,'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 m=images['PreviewsXcode'];n=images['PreviewsIDEAPI']
 def got(a):
  s=next(s for s in m.sections if s['vm']<=a<s['vm']+s['length']);assert s['flags']&255==6
  return m.symbols[m.indirect[s['r1']+(a-s['vm'])//8]]
 notifications={hex(a):got(a) for a in [0x330760,0x330758]}
 assert notifications=={'0x330760':'_IDEBuildOperationWillStartNotification','0x330758':'_IDEBuildOperationDidStopNotification'}
 calls=[]
 expected={0x16c7b4:'_objc_msgSend$dvt_addObserverForName:object:queue:usingBlock:',0x16c870:'_objc_msgSend$dvt_addObserverForName:object:queue:usingBlock:',0x16ed78:'_$s10Foundation12NotificationV6objectypSgvg',0x16ef88:'_$s10Foundation12NotificationV6objectypSgvg',0x16edb8:'_swift_dynamicCast',0x16efc8:'_swift_dynamicCast',0x16edc8:'_objc_msgSend$executionEnvironment',0x16efd8:'_objc_msgSend$executionEnvironment',0x16edd8:'_objc_msgSend$workspace',0x16efe8:'_objc_msgSend$workspace',0x16ee38:'_$sSo8NSObjectC10ObjectiveCE2eeoiySbAB_ABtFZ',0x16f048:'_$sSo8NSObjectC10ObjectiveCE2eeoiySbAB_ABtFZ',0x16ee74:'_$sSo17IDEBuildOperationC14PreviewsIDEAPIE02isC5BuildSbvg',0x16f084:'_objc_msgSend$result',0x16eecc:'_$s22PreviewsFoundationHost20SubscriberCollectionV9notifyAll7closureyyxXE_tF',0x16f0e0:'_$s22PreviewsFoundationHost20SubscriberCollectionV9notifyAll7closureyyxXE_tF'}
 for a,name in expected.items():
  t=m.resolve(m.branch(a));assert name in ([t['name']] if t['kind']=='import_stub' else t['names']),(hex(a),t);calls.append({'call':hex(a),'target':t})
 classifier=n.resolve(n.branch(0x8fbc));assert '_objc_msgSend$buildCommand' in ([classifier['name']] if classifier['kind']=='import_stub' else classifier['names'])
 # Selected semantic anchors. Full bounded ranges are byte-compared above.
 for a,v in {0x16ee78:0x92400014,0x16eeac:0xf81a03b4,0x16eeb0:0x52800068,0x16eeb4:0x381a83a8,0x16f088:0xf100041f,0x16f08c:0x1a9f17f4,0x16f0c0:0xf81a03b4,0x16f0c4:0x52800088,0x16f0c8:0x381a83a8,0x16c7a8:0xd2800003,0x16c7ac:0xd2800004,0x16c864:0xd2800003,0x16c868:0xd2800004}.items():assert m.word(a)==v,hex(a)
 assert n.word(0x8fc0)==0xf100201f and n.word(0x8fc4)==0x1a9f17e0
 assert m.branch(0x16f428)==0x16ed0c and m.branch(0x16f430)==0x16ef1c and m.branch(0x16f5a0)==0x16f478
 assert any('sendEvent' in s for s in m.named[0x16f478])
 assert any('IDEBuildOperationCML' in s for s in m.named[0x35e330])
 for a,name in [(0x366f10,'buildStartedToken'),(0x366f18,'buildCompletedToken'),(0x366eb0,'observers')]:assert any(name in s for s in m.named[a])
 result={'images':{k:{'sha256':hashlib.sha256(v.data).hexdigest(),'uuid':v.uuid,'architecture':'arm64'} for k,v in images.items()},'ranges':ranges,'source_bytes_verified':sum(r['bytes'] for r in ranges),'notification_imports':notifications,'calls':calls,'classifier_call':n.resolve(n.branch(0x8fbc)),'source_policy':{'registration':'Default notification center; object and queue nil; separate buildStartedToken/buildCompletedToken stores. Forwarders bind start/stop callbacks.','guard':'Notification.object conditional cast to IDEBuildOperation; operation.executionEnvironment.workspace compared with listener workspace using imported NSObject equality. Both absent passes; one absent or unequal rejects.','start':'isPreviewsBuild imported getter returns buildCommand == 8. Low bit stored as payload with tag 3 and sent through SubscriberCollection.notifyAll.','stop':'operation.result == 1 stored as payload with tag 4 and sent through the same subscriber forwarding entry. The semantic result enum name is not established.','prior_handler_correlation':'Previously recovered event metadata names tags 3/4 buildSystemBuildStarted/buildSystemBuildStopped. Prior build-time-gate source assigns timestamp for both start flag values; preview-build true exits after timestamp, false invalidates builder/coalescer and optionally requests workspaceChanged then pauses userInitiatedBuild.'},'scope':{'static_only':True,'private_native_calls':0,'native_event_delivery_observed':False,'result_enum_semantics_known':False,'build_stop_consumer_qualified':False,'complete_refresh_behavior':False,'full_canvas_parity':False},'failures':['Initial metadata query had no candidates due to narrow symbol spelling; no absence inference.','Ambient sandbox denied opening controller lock; authorized escalated locked route succeeded.','First verifier assumed Objective-C selector stubs were import-table entries; actual defined selector-stub symbol binding used instead.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls_bound':len(calls)+1}))
