from pathlib import Path
import subprocess,json,plistlib,hashlib,struct,importlib.util
w=Path(__file__).parent
root=Path('/Users/8amps/xcpreviewer-rs')
script=root/'tools/re/swiftui-preview/capture.py'
spec=importlib.util.spec_from_file_location('capture',script);capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
rows=[]
for case,selection in [('provider',['--provider','Fixtures.Bars']),('factory',[])]:
 args=['python3',str(script),str(w/'Provider.swift'),'--width','48','--height','32','--scale','2','--output',str(w/(case+'.bplist')),'--reference-png',str(w/(case+'.png'))]+selection
 r=subprocess.run(args,capture_output=True,timeout=50)
 (w/(case+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==0,r.stderr.decode()
 receipt=json.loads(r.stdout);rows.append(receipt)
 (w/(case+'.json')).write_bytes(r.stdout)
a=(w/'provider.bplist').read_bytes();b=(w/'factory.bplist').read_bytes()
assert plistlib.loads(a)==plistlib.loads(b)
p=plistlib.loads(a);pixels=p['bitmapDescription']['data']
assert len(pixels)==96*64*4
# Full raster orientation and explicit color controls, not a few sampled pixels.
assert pixels==(bytes([0,0,255,255])*96*32+bytes([255,0,0,255])*96*32)
before=hashlib.sha256(a).hexdigest()
for case,extra,diagnostic in [('nonprovider',['--provider','NotProvider'],'PreviewProvider'),('ambiguous',['--provider','Fixtures.Bars','--factory','makePreview'],'not allowed'),('invalid',['--provider','Fixtures.Bars()'],'qualified identifier'),('empty',['--provider',''],'qualified identifier')]:
 r=subprocess.run(['python3',str(script),str(w/'Provider.swift'),'--output',str(w/'provider.bplist')]+extra,capture_output=True,timeout=50)
 (w/(case+'.stderr')).write_bytes(r.stderr)
 assert r.returncode!=0 and diagnostic in r.stderr.decode(),r.stderr.decode()
 assert hashlib.sha256((w/'provider.bplist').read_bytes()).hexdigest()==before
rows.append({'negative_controls':4,'payload_preserved':True,'full_raster_bytes':len(pixels),'provider_factory_equal':True})
(w/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows[-1]))
