import hashlib,importlib.util,json,shutil,sys,tempfile
from pathlib import Path
root=Path('/Users/8amps/xcpreviewer-rs');here=Path(__file__).parent;source=root/'research/evidence/surface-full-reuse-2026-10-11'
old=json.loads((source/'manifest.json').read_text())
if hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest()!='3882895c02cd09939282f3d1c8867c5726e236a094d4107617201afe39988d6a':raise ValueError('Prior seal changed')
if not all(hashlib.sha256((source/n).read_bytes()).hexdigest()==v['sha256'] and len((source/n).read_bytes())==v['bytes'] for n,v in old['files'].items()):raise ValueError('Prior bytes changed')
spec=importlib.util.spec_from_file_location('reader',here/sys.argv[1]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
results=[]
for fault in ['positive','float_ids','float_pids','false_wait','padding','tail']:
 with tempfile.TemporaryDirectory(prefix='owned-r2-frozen-') as tmp:
  e=Path(tmp)/'e';shutil.copytree(source,e);p=e/'wait.json';d=json.loads(p.read_text());rows=[json.loads(x) for x in d['stdout'].splitlines()]
  if fault=='false_wait':d['code']=False
  for row,mode in zip(rows,['reuse','separate']):
   q=e/mode/'receiver.json';peer=json.loads(q.read_text())
   if fault=='float_ids':
    for obj in [row,peer]:
     for k in obj:
      if k in ['first_id','second_id','live_global_first','live_global_second','final_global_first','final_global_second','settled_global_first','settled_global_second','first_lookup_after_release','remaining_lookup','retired_first_lookup','retired_second_lookup']:obj[k]=float(obj[k]) if obj[k]!=0 else obj[k]
   if fault=='float_pids':
    for obj in [row,peer]:
     for k in ['sender_pid','receiver_pid']:
      if k in obj:obj[k]=float(obj[k])
   q.write_text(json.dumps(peer))
  if fault in ['padding','tail']:
   q=e/'reuse/after-right-release.bin';b=bytearray(q.read_bytes());b[68 if fault=='padding' else 16383]^=1;q.write_bytes(b)
  d['stdout']=''.join(json.dumps(x)+'\n' for x in rows);p.write_text(json.dumps(d))
  (e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
  try:result=module.verify(e);accepted=True
  except (ValueError,AssertionError,KeyError,TypeError):accepted=False;result=None
  results.append({'fault':fault,'accepted':accepted,'result':result})
print(json.dumps({'optimized':not __debug__,'verifier':sys.argv[1],'cases':results},indent=2))
