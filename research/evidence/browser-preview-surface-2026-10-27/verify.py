from pathlib import Path
import json,hashlib,tempfile,shutil,subprocess
r=Path(__file__).resolve().parents[3];e=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for row in json.loads((e/'seal.json').read_text())['files']:assert sha(e/row['path'])==row['sha256']
for p,h in json.loads((e/'implementation-pins.json').read_text()).items():assert sha(r/p)==h
w=Path(tempfile.mkdtemp(prefix='browser-preview-replay-',dir='/private/tmp'));(w/'native').mkdir()
for n in ['build.py','check.py','worker-check.cjs']:shutil.copy2(e/n,w/n)
for n in ['native.swift','bridge.h','bridge.s','identity.c','run-native.py','source-verify.py','input.bplist']:shutil.copy2(e/n,w/'native'/n)
for name,args in [('source',['python3',str(w/'native/source-verify.py')]),('native',['python3',str(w/'native/run-native.py')]),('build',['python3',str(w/'build.py')]),('check',['python3',str(w/'check.py'),'--replay'])]:
 p=subprocess.run(args,cwd=r,capture_output=True,timeout=180);(w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr);print(name,p.returncode,flush=True);p.check_returncode()
a=json.loads((w/'results.json').read_text());b=json.loads((e/'results.json').read_text());assert a.pop('rust_tests')==2;assert b.pop('rust_tests')==399;assert a==b
print(w,flush=True)
