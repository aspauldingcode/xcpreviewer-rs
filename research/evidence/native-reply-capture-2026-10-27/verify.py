from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
here=Path(__file__).resolve().parent
for name,digest in json.loads((here/'pins.json').read_text()).items(): assert hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,name
work=Path(tempfile.mkdtemp(prefix='native-reply-capture-replay-'))
for name in ['native.swift','bridge.s','bridge.h','identity.c','peer.m','run.py','check.py','source-verify.py','connection-source-verify.py']:
 shutil.copyfile(here/name,work/name)
for name,deadline in [('source-verify.py',60),('run.py',180),('check.py',10)]:
 r=subprocess.run(['python3',str(work/name)],capture_output=True,timeout=deadline)
 (work/(name+'.stdout')).write_bytes(r.stdout);(work/(name+'.stderr')).write_bytes(r.stderr);r.check_returncode()
print(json.dumps({'passed':True,'workspace':str(work)}))
