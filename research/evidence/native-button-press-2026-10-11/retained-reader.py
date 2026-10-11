import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 failed=json.loads((e/'retained-compile-failure/compile.json').read_text());assert failed['code']==1 and failed['timeout'] is False and 'concrete type' in failed['stderr'];good=json.loads((e/'compile.json').read_text());assert good['code']==0 and good['timeout'] is False
 env=json.loads((e/'environment.json').read_text());rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==env['helper_sha256'];assert rea['identity']['result']['path']==env['helper'] and rea['identity']['result']['architecture']=='arm64' and rea['closed']['result'] is None
 expected=(bytes([255,0,0,255])*17+bytes([165])*12)*9+bytes([195])*(16384-720);total=0
 for i in range(2):
  root=e/f'run-{i}';assert json.loads((root/'wait.json').read_text())=={'code':0,'timeout':False,'stdout':'','stderr':''};d=json.loads((root/'result.json').read_text());assert d['owned_windows']==0 and d['button_found'] is False and d['presses']==[] and d['roles']==['AXGroup'] and d['inspected']==1 and len(d['rows'])==1
  row=d['rows'][0];assert row['phase']=='initial' and row['model_blue'] is False
  for k,v in {'width':17,'height':9,'stride':80,'allocation_bytes':16384,'bitmap_info':16385,'alpha_info':1,'bits_per_component':8,'bits_per_pixel':32,'callbacks':1,'size':[17,9],'color_space':'kCGColorSpaceSRGB'}.items():assert row[k]==v and type(row[k]) is type(v)
  raw=(root/'initial.raw').read_bytes();assert raw==expected;total+=len(raw)
 assessment=json.loads((e/'assessment.json').read_text());assert assessment['input_acceptance'] is False and assessment['delivered_presses']==0
 return {'allocation_bytes':total,'delivered_presses':0}
