import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 total=0
 for mode in ['baseline','fixed']:
  for stream in ['stdout','stderr']:
   root=e/mode/stream;wait=json.loads((root/'wait.json').read_text());fixed=mode=='fixed';assert wait['code']==(-25 if fixed else 0) and wait['timeout'] is False and wait['reaped'] is True
   assert wait['parent_limit_before']==wait['parent_limit_after']==[9223372036854775807,9223372036854775807];assert json.loads((root/'child.json').read_text())['file_limit']==([4096,4096] if fixed else [9223372036854775807,9223372036854775807])
   raw=bytes.fromhex(wait[stream]);assert raw==b'Z'*(4096 if fixed else 8192);assert bytes.fromhex(wait['stderr' if stream=='stdout' else 'stdout'])==b'';total+=len(raw)
   assert wait['error']==('Compiler output/file size limit exceeded' if fixed else None)
 assert total==24576
 return {'producer_count':4,'complete_diagnostic_bytes':total}
