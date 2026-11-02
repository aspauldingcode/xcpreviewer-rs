from pathlib import Path
import json,hashlib,subprocess,tempfile,shutil
here=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in json.loads((here/'pins.json').read_text()).items():assert sha(here/name)==digest,name
work=Path(tempfile.mkdtemp(prefix='native-reply-fd-envelope-replay-'))
for n in json.loads((here/'pins.json').read_text()):shutil.copyfile(here/n,work/n)
for name,deadline in [('source-verify.py',60),('callback-imports.py',30),('run.py',180),('check.py',10)]:
 p=subprocess.run(['python3',str(work/name)],capture_output=True,timeout=deadline);(work/(name+'.stdout')).write_bytes(p.stdout);(work/(name+'.stderr')).write_bytes(p.stderr);p.check_returncode()
print(json.dumps({'passed':True,'workspace':str(work)}))
