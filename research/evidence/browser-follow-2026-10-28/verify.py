from pathlib import Path
import json,hashlib,tempfile,shutil,subprocess
here=Path(__file__).parent;r=here.parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in json.loads((here/'pins.json').read_text()).items():assert sha(r/name)==digest,name
runtime=json.loads((here/'runtime.json').read_text());assert sha(Path(runtime['wasm']))==runtime['wasm_sha256']
work=Path(tempfile.mkdtemp(prefix='browser-follow-evidence-replay-'))
for n in ['check.py','live.png']+[f'browser-{n}.json' for n in ['initial','transparent','invalid','recovered','stopped','live']]:shutil.copyfile(here/n,work/n)
p=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=30);(work/'verify.stdout').write_bytes(p.stdout);(work/'verify.stderr').write_bytes(p.stderr);p.check_returncode()
print(json.dumps({'passed':True,'workspace':str(work),'scope':'Copied-source reader/scheduler replay plus retained browser receipt/native-PNG checks; not a new browser interaction replay.'}))
