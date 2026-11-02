from pathlib import Path
import json,hashlib,shutil,subprocess,tempfile
here=Path(__file__).resolve().parent;root=here.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in json.loads((here/'pins.json').read_text()).items(): assert sha(root/name)==digest,name
for name,digest in json.loads((here/'transport-results.json').read_text())['dependencies'].items(): assert sha(Path(name))==digest,name
work=Path(tempfile.mkdtemp(prefix='swiftui-registry-capture-replay-'))
for name in ['Source.swift','Controls.swift','Traits.swift','Provider.swift','source.py','check-capture.py','check-transport.py','check-guard.py']:
 shutil.copyfile(here/name,work/name)
for name,deadline in [('source.py',60),('check-capture.py',600),('check-guard.py',120),('check-transport.py',60)]:
 result=subprocess.run(['python3',str(work/name)],capture_output=True,timeout=deadline)
 (work/(name+'.stdout')).write_bytes(result.stdout);(work/(name+'.stderr')).write_bytes(result.stderr);result.check_returncode()
print(json.dumps({'passed':True,'workspace':str(work)}))
