from pathlib import Path
import json,hashlib,tempfile,shutil,subprocess
here=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins=json.loads((here/'pins.json').read_text())
for n,d in pins['owned'].items():assert sha(here/n)==d,n
for n,d in pins['source_verifier'].items():assert sha(r/n)==d,n
work=Path(tempfile.mkdtemp(prefix='uv-fd-encode-replay-'))
for n in pins['owned']:shutil.copyfile(here/n,work/n)
for name,deadline in [('run.py',120),('check.py',10)]:
 p=subprocess.run(['python3',str(work/name)],capture_output=True,timeout=deadline);(work/(name+'.stdout')).write_bytes(p.stdout);(work/(name+'.stderr')).write_bytes(p.stderr);p.check_returncode()
print(json.dumps({'passed':True,'workspace':str(work)}))
