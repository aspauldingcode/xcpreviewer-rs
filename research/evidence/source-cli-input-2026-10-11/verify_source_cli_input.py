import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 pids=[]
 for mode,fixed in [('baseline',False),('fixed',True)]:
  root=e/mode;assert json.loads((root/'wait.json').read_text())=={'code':0,'stdout':'','stderr':'','timeout':False};d=json.loads((root/'process/result.json').read_text());assert d['fixed'] is fixed and [x['kind'] for x in d['records']]==['fifo','symlink']
  for row in d['records']:
   hung=not fixed and row['kind']=='fifo';assert row['wait']=={'code':-9 if hung else 1,'timeout':hung,'reaped':True};assert type(row['pid']) is int and row['pid']>0;pids.append(row['pid']);assert row['stdout']=='' and row['cache_created'] is False and row['output_created'] is False
   sub=root/'process'/row['kind'];assert not (sub/'owned.swift').exists() and not (sub/'owned.swift').is_symlink();assert not (sub/'cache').exists() and not (sub/'output').exists()
   if hung:assert row['stderr']==''
   else:
    error=json.loads(row['stderr']);assert error['ok'] is False
    if row['kind']=='fifo':assert error=={'ok':False,'error_type':'ValueError','error':'Bounded regular source file required'}
    elif not fixed:assert error=={'ok':False,'error_type':'ValueError','error':'Unsupported expression outside primary-layer ZStack.frame contract'}
    else:assert error['error_type']=='OSError' and error['error'].startswith('[Errno 62] Too many levels of symbolic links: ')
   if row['kind']=='symlink':assert (sub/'target.swift').read_bytes()==b'Text("owned unsupported")'
 assert len(set(pids))==4 and json.loads((e/'assessment.json').read_text())['baseline_acceptance'] is False
 return {'actual_cli_processes':4,'compiler_invocations':0}
