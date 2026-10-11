import hashlib,json
from pathlib import Path
PHASES=['initial','repeat','changed-immediate','changed-drained','fresh-same-model','reset-immediate','reset-drained','fresh-default-model']
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 failed=json.loads((e/'retained-compile-failure/compile.json').read_text());assert failed['code']==1 and failed['timeout'] is False and 'unable to load standard library' in failed['stderr'];good=json.loads((e/'compile.json').read_text());assert good['code']==0 and good['timeout'] is False
 env=json.loads((e/'environment.json').read_text());rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==env['helper_sha256'];assert rea['identity']['result']['path']==env['helper'] and rea['identity']['result']['architecture']=='arm64' and rea['closed']['result'] is None
 total=0;allocations=[]
 for run in range(2):
  root=e/f'run-{run}';assert json.loads((root/'wait.json').read_text())=={'code':0,'timeout':False,'stdout':'','stderr':''};d=json.loads((root/'result.json').read_text());assert d['owned_windows']==0 and [x['phase'] for x in d['rows']]==PHASES
  original=d['rows'][0];newrenderer=d['rows'][4];newmodel=d['rows'][7];assert original['renderer_identity']!=newrenderer['renderer_identity'] and original['model_identity']==newrenderer['model_identity'];assert newmodel['model_identity']!=original['model_identity'] and newmodel['renderer_identity'] not in [original['renderer_identity'],newrenderer['renderer_identity']]
  for i,row in enumerate(d['rows']):
   blue=i in [2,3,4];assert row['model_blue'] is blue
   if i not in [4,7]:assert row['model_identity']==original['model_identity'] and row['renderer_identity']==original['renderer_identity']
   for key,value in {'width':17,'height':9,'stride':80,'allocation_bytes':16384,'bitmap_info':16385,'alpha_info':1,'bits_per_component':8,'bits_per_pixel':32,'color_space':'kCGColorSpaceSRGB','callbacks':1,'size':[17,9]}.items():assert row[key]==value and (type(row[key]) is type(value))
   pixel=bytes([0,0,255,255] if blue else [255,0,0,255]);expected=(pixel*17+bytes([165])*12)*9+bytes([195])*(16384-720);raw=(root/(row['phase']+'.raw')).read_bytes();assert raw==expected;allocations.append(raw);total+=len(raw)
 for i in range(8):assert allocations[i]==allocations[i+8]
 assert total==262144
 return {'frames':16,'allocation_bytes':total,'padding_bytes':1728,'tail_bytes':250624,'native_runs':2}
