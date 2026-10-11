import hashlib,json,re
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 good=json.loads((e/'compile.json').read_text());assert good['code']==0 and good['timeout'] is False
 env=json.loads((e/'environment.json').read_text());rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==env['helper_sha256'];assert rea['identity']['result']['path']==env['helper'] and rea['identity']['result']['architecture']=='arm64' and rea['closed']['result'] is None
 source=(e/'PlacementButtonPressReference.swift').read_text();assert 'guard let screen=NSScreen.main else { throw NSError(domain:"OwnedState",code:3) }' in source
 for i in range(2):
  root=e/f'run-{i}';assert {p.name for p in root.iterdir()}=={'wait.json'}
  wait=json.loads((root/'wait.json').read_text());assert wait['code']==-5 and wait['timeout'] is False and wait['stdout']==''
  assert re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} placement-button-press-reference\[[0-9]+:[0-9]+\] ApplePersistence=NO\nSwift/ErrorType.swift:254: Fatal error: Error raised at top level: Error Domain=OwnedState Code=3 "\(null\)"\n',wait['stderr'])
 a=json.loads((e/'assessment.json').read_text());assert a['input_acceptance'] is False and a['delivered_presses_observed']==0 and a['frame_bytes_observed']==0 and a['cleanup_verified'] is False
 return {'native_failures':2,'frame_bytes_observed':0,'input_acceptance':False}
