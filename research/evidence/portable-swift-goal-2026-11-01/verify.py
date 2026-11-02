from pathlib import Path
import json,hashlib,tempfile,subprocess,shutil
here=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins=json.loads((here/'pins.json').read_text());work=Path(tempfile.mkdtemp(prefix='portable-swift-goal-replay-'))
for n,d in pins.items():assert sha(here/n)==d,n;shutil.copyfile(here/n,work/n)
for n,deadline in [('probe.py',140),('check.py',20)]:
 p=subprocess.run(['python3',str(work/n)],capture_output=True,timeout=deadline);(work/(n+'.stdout')).write_bytes(p.stdout);(work/(n+'.stderr')).write_bytes(p.stderr);p.check_returncode()
print(json.dumps({'passed':True,'workspace':str(work)}))
