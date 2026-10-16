import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path('/Users/8amps/xcpreviewer-rs');src=root/'research/evidence/surface-send-destroy-2026-10-14';out=Path(__file__).parent
expected='bc202e0c981843dd6af7f4c536c5bfc54e1c77c4290526839e9753fdb3699c4c'
if hashlib.sha256((src/'manifest.json').read_bytes()).hexdigest()!=expected:raise ValueError('Prior manifest changed')
manifest=json.loads((src/'manifest.json').read_text())
if not all(len((src/n).read_bytes())==x['bytes'] and hashlib.sha256((src/n).read_bytes()).hexdigest()==x['sha256'] for n,x in manifest['files'].items()):raise ValueError('Prior evidence changed')
rows=[]
for fault in ['padding','tail','refs','nonzero_wait']:
 with tempfile.TemporaryDirectory(prefix='owned-r1-frozen-') as tmp:
  e=Path(tmp)/'e';shutil.copytree(src,e)
  if fault in ['padding','tail']:
   p=e/'move/alias-after-right-release.bin';b=bytearray(p.read_bytes());b[68 if fault=='padding' else 16383]^=1;p.write_bytes(b)
  elif fault=='refs':
   p=e/'move/stdout.jsonl';v=[json.loads(x) for x in p.read_text().splitlines()];v[1]['returned_refs']=1;p.write_text(''.join(json.dumps(x)+'\n' for x in v))
  else:(e/'move/wait.json').write_text(json.dumps({'code':42,'timeout':False}))
  (e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
  for optimized in [False,True]:
   code='import sys;sys.path.insert(0,'+repr(str(out))+');from verify_surface_send_destroy import verify;print(verify('+repr(str(e))+'))'
   p=subprocess.run([sys.executable,*(['-O'] if optimized else []),'-c',code],capture_output=True,text=True,timeout=10)
   rows.append({'fault':fault,'optimized':optimized,'exit':p.returncode,'accepted':p.returncode==0,'stdout':p.stdout,'stderr':p.stderr})
(out/'repaired-counterexamples.json').write_text(json.dumps({'prior_manifest':expected,'cases':rows},indent=2)+'\n')
print(json.dumps([{'fault':x['fault'],'optimized':x['optimized'],'accepted':x['accepted']} for x in rows]))
