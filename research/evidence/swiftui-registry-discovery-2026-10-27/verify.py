from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
here=Path(__file__).resolve().parent;root=here.parents[2]
for name,digest in json.loads((here/'pins.json').read_text()).items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
work=Path(tempfile.mkdtemp(prefix='swiftui-registry-replay-'))
for name in ['Controls.swift','None.swift','Invalid.swift','Slow.swift','check.py']:
 shutil.copyfile(here/name,work/name)
r=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=240)
(work/'check.stdout').write_bytes(r.stdout);(work/'check.stderr').write_bytes(r.stderr);r.check_returncode()
print(json.dumps({'passed':True,'workspace':str(work)}))
