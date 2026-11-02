from pathlib import Path
import hashlib,json,tempfile,subprocess,shutil
here=Path(__file__).parent
for n,d in json.loads((here/'pins.json').read_text()).items():assert hashlib.sha256((here/n).read_bytes()).hexdigest()==d,n
work=Path(tempfile.mkdtemp(prefix='canvas-observer-removal-replay-'))
for n in ['source.py','macho.py']:shutil.copyfile(here/n,work/n)
p=subprocess.run(['python3',str(work/'source.py')],capture_output=True,timeout=55)
(work/'stdout').write_bytes(p.stdout);(work/'stderr').write_bytes(p.stderr);p.check_returncode()
assert json.loads((work/'findings.json').read_text())==json.loads((here/'findings.json').read_text())
print(json.dumps({'passed':True,'workspace':str(work),'scope':'Fresh static source replay only; actual lifetime and cancellation not observed.'}))
