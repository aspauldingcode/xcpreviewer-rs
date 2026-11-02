from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,shutil,os
here=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (here/'pins.json').exists():
 for name,digest in json.loads((here/'pins.json').read_text()).items():assert sha(r/name)==digest,name
if (here/'transport-results.json').exists():
 for name,digest in json.loads((here/'transport-results.json').read_text())['dependencies'].items():assert sha(Path(name))==digest,name
work=Path(tempfile.mkdtemp(prefix='swiftui-watch-replay-'));root=work/'root';tools=root/'tools/re/swiftui-preview';tools.mkdir(parents=True);tests=root/'tools/re/tests';tests.mkdir()
for name in ['capture.py','discover.py','watch.py','Capture.swift.template','Registry.swift','RegistryBridge.s','RegistryBridge.h','RegistryIdentity.c']:shutil.copyfile(r/'tools/re/swiftui-preview'/name,tools/name)
shutil.copyfile(r/'tools/re/tests/test_swiftui_watch.py',tests/'test_swiftui_watch.py')
for name in ['verify.py','registry.py','transport.py']:shutil.copyfile(here/name,work/name)
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
commands=[('unit',[sys.executable,'-m','unittest','discover','-s',str(tests),'-p','test_swiftui_watch.py','-v'],10),('watch',[sys.executable,str(work/'verify.py'),str(root)],240),('registry',[sys.executable,str(work/'registry.py'),str(root)],240),('transport',[sys.executable,str(work/'transport.py')],30)]
for name,args,deadline in commands:
 p=subprocess.run(args,capture_output=True,timeout=deadline,env=env);(work/(name+'-replay.stdout')).write_bytes(p.stdout);(work/(name+'-replay.stderr')).write_bytes(p.stderr);assert p.returncode==0,(name,p.stdout.decode(),p.stderr.decode())
print(json.dumps({'passed':True,'workspace':str(work),'copied_product_sources':True}))
