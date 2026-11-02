from pathlib import Path
import hashlib,json,subprocess,tempfile,shutil
here=Path(__file__).parent
for n,d in json.loads((here/'pins.json').read_text()).items():assert hashlib.sha256((here/n).read_bytes()).hexdigest()==d,n
work=Path(tempfile.mkdtemp(prefix='canvas-project-binding-replay-'));shutil.copyfile(here/'source.py',work/'source.py')
p=subprocess.run(['python3',str(work/'source.py')],capture_output=True,timeout=90);(work/'verify.stdout').write_bytes(p.stdout);(work/'verify.stderr').write_bytes(p.stderr);p.check_returncode();assert json.loads((work/'findings.json').read_text())==json.loads((here/'findings.json').read_text())
print(json.dumps({'passed':True,'workspace':str(work),'scope':'Source-only identity/byte/selector verification; no native project runtime invocation.'}))
