import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 pids=[];expected=b'\0asm\x01\0\0\0owned module';total=0
 for mode,kind in [('baseline','view.ll'),('baseline','view.wasm'),('fixed','view.ll'),('fixed','view.wasm')]:
  root=e/mode/kind;wait=json.loads((root/'wait.json').read_text());hung=mode=='baseline';assert wait['code']==(-9 if hung else 0) and wait['timeout'] is hung and wait['reaped'] is True and wait['stderr']=='' and wait['stdout']==('entered\n' if hung else 'entered\nrejected\n');pids.append(wait['pid'])
  before=json.loads((root/'before.json').read_text());assert before['kind']==kind and before['receipt']['cache_hit'] is False and len(before['calls'])==2;assert bytes.fromhex(before['module_hex'])==expected;total+=len(expected)
  receipt=json.loads(bytes.fromhex(before['pointer_hex']));assert receipt['module_sha256']==hashlib.sha256(expected).hexdigest();assert (root/'output'/receipt['module']).read_bytes()==expected and (root/'output/current.json').read_bytes()==bytes.fromhex(before['pointer_hex']);assert not Path(before['bad_path']).name.startswith('.')
  if hung:assert not (root/'after.json').exists()
  else:
   after=json.loads((root/'after.json').read_text());assert after['error_type']=='ValueError' and after['error']=='Bounded regular cache metadata required';assert after['calls']==before['calls'] and after['pointer_hex']==before['pointer_hex'] and after['module_hex']==before['module_hex'];total+=len(expected)
 assert len(set(pids))==4 and total==120
 return {'actual_producers':4,'complete_module_bytes':total,'scope':'explicit fake compiler cache mechanics only'}
