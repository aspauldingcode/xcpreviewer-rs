from pathlib import Path
import sys,subprocess,resource,json,hashlib
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 raw=Path(sys.argv[1]).resolve();assert str(raw).startswith('/private/tmp/') or str(raw).startswith(str(r/'research/raw')+'/');raw.mkdir(parents=True,exist_ok=False);clang='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
 for name in ['interaction','windowcheck']:
  (raw/(name+'.m')).write_text((w/(name+'.m')).read_text())
  p=subprocess.run([clang,'-Wall','-Wextra','-Werror',str(w/(name+'.m')),'-framework','AppKit','-framework','CoreGraphics','-o',str(w/name)],capture_output=True,timeout=30);(raw/(name+'-build.log')).write_bytes(p.stdout+p.stderr);p.check_returncode()
 child=subprocess.Popen([str(w/'interaction'),str(raw)],cwd=w,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 timed_out=False
 try:out,err=child.communicate(timeout=15)
 except subprocess.TimeoutExpired:
  child.kill();out,err=child.communicate();timed_out=True;(raw/'timeout.json').write_text(json.dumps({'pid':child.pid,'returncode':child.returncode}))
 (raw/'interaction.stdout').write_bytes(out);(raw/'interaction.stderr').write_bytes(err)
 p=subprocess.run([str(w/'windowcheck'),str(child.pid)],capture_output=True,timeout=4);(raw/'window-cleanup.json').write_bytes(p.stdout);(raw/'window-check.stderr').write_bytes(p.stderr);p.check_returncode();assert not timed_out and child.returncode==0,(child.returncode,err)
 result=json.loads(out);assert result['clicks']==1 and result['all_event_bytes_roundtrip_equal']==256 and result['changed_frame'] and not result['native_canvas_protocol_observed']
 counts=0
 for name,rgba in [('before.bin',[234,51,35,255]),('repeat.bin',[234,51,35,255]),('after.bin',[0,0,245,255]),('after-repeat.bin',[0,0,245,255])]:
  b=(raw/name).read_bytes();assert len(b)==38400 and b==bytes(rgba)*9600;counts+=len(b)
 for n in range(4):
  b=(raw/f'srgb-{n}.bin').read_bytes();assert len(b)==38400 and b==bytes([255,0,0,255] if n<2 else [0,0,255,255])*9600;counts+=len(b)
 icc=(raw/'capture.icc').read_bytes();assert icc[36:40]==b'acsp' and icc[16:20]==b'RGB ';certificate={'capture_icc_sha256':hashlib.sha256(icc).hexdigest(),'capture_icc_bytes':len(icc),'independent_pixel_bytes_equal':counts,'private_public_event_bytes_equal':256,'owned_native_clicks':1,'profile_raw_rgba_before':[234,51,35,255],'profile_raw_rgba_after':[0,0,245,255],'export_srgb_before':[255,0,0,255],'export_srgb_after':[0,0,255,255],'bitmap':{'width':120,'height':80,'stride':480,'bits':8,'samples':4,'format':0,'padding_bytes':0},'window_cleanup':json.loads(p.stdout),'native_canvas_protocol_observed':False,'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in raw.glob('*.bin')}}
 (raw/'verification.json').write_text(json.dumps(certificate,indent=2)+'\n');print(json.dumps(result));print(json.dumps(certificate))
