from pathlib import Path
import hashlib,json,tempfile,subprocess,shutil
here=Path(__file__).parent
for n,d in json.loads((here/'pins.json').read_text()).items():assert hashlib.sha256((here/n).read_bytes()).hexdigest()==d,n
work=Path(tempfile.mkdtemp(prefix='canvas-workspace-caller-replay-'))
for n in ['source.py','macho.py','ui.py','native-ui-projection.json']:shutil.copyfile(here/n,work/n)
for n,deadline in [('source.py',120),('ui.py',10)]:
 p=subprocess.run(['python3',str(work/n)],capture_output=True,timeout=deadline);(work/(n+'.stdout')).write_bytes(p.stdout);(work/(n+'.stderr')).write_bytes(p.stderr);p.check_returncode()
assert json.loads((work/'findings.json').read_text())==json.loads((here/'findings.json').read_text())
print(json.dumps({'passed':True,'workspace':str(work),'scope':'Fresh static source plus retained UI projection consistency; no new native UI observation.'}))
