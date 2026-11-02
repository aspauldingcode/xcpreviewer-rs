from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
here=Path(__file__).resolve().parent
root=here.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in json.loads((here/'pins.json').read_text()).items():
 assert sha(root/name)==digest,name
for name,digest in json.loads((here/'transport-results.json').read_text())['dependencies'].items():
 assert sha(Path(name))==digest,name
work=Path(tempfile.mkdtemp(prefix='swiftui-provider-replay-'))
for name in ['Provider.swift','check.py','check-transport.py']:
 shutil.copyfile(here/name,work/name)
for name in ['check.py','check-transport.py']:
 result=subprocess.run(['python3',str(work/name)],capture_output=True,timeout=180)
 (work/(name+'.stdout')).write_bytes(result.stdout)
 (work/(name+'.stderr')).write_bytes(result.stderr)
 result.check_returncode()
print(json.dumps({'passed':True,'workspace':str(work)}))
