from pathlib import Path
import hashlib,json,tempfile,urllib.request,subprocess,shutil
here=Path(__file__).parent;manifest=json.loads((here/'sources.json').read_text());work=Path(tempfile.mkdtemp(prefix='omarchy-basis-review-replay-'))
(work/'sources.json').write_text(json.dumps(manifest));shutil.copyfile(here/'audit.py',work/'audit.py')
for row in manifest['files']:
 with urllib.request.urlopen(row['url'],timeout=15) as response:data=response.read(2*1024*1024+1)
 assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
 p=work/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
p=subprocess.run(['python3',str(work/'audit.py')],capture_output=True,timeout=10);(work/'audit.stdout').write_bytes(p.stdout);(work/'audit.stderr').write_bytes(p.stderr);p.check_returncode();assert json.loads((work/'review.json').read_text())==json.loads((here/'review.json').read_text())
print(json.dumps({'passed':True,'workspace':str(work),'upstream_code_executed':False}))
