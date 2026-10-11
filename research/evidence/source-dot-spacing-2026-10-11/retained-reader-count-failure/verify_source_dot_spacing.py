"""Independent reader for native member-access spacing controls."""
import hashlib,json
from pathlib import Path
COMPILER_SHA='2ed38571e92c0283091838c1649e27650ad9c99950288e883c7b2dc6c4ce89fb'
PRIMARY='ZStack {\nColor(.sRGB, red: 0, green: 0, blue: 1, opacity: 1.0)\nColor(.sRGB, red: 1, green: 0, blue: 0, opacity: 0.5)\nColor(.sRGB, red: 0, green: 1, blue: 0, opacity: 0.25)\n}.frame(width: 17, height: 9)\n'
OPAQUE='Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 17, height: 9)'
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 env=json.loads((e/'environment.json').read_text());assert env['compiler_sha256']==COMPILER_SHA
 rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==COMPILER_SHA;assert rea['identity']['result']['path']==env['compiler_path'] and rea['identity']['result']['architecture']=='arm64';assert rea['closed']['result'] is None
 rows=json.loads((e/'observations.json').read_text());assert len(rows)==4
 for i,(row,(label,space)) in enumerate(zip(rows,[('normal',''),('space',' '),('tab','\t'),('newline','\n')])):
  assert row['index']==i and row['label']==label and row['space_hex']==space.encode().hex();assert row['wait']=={'code':0 if i==0 else 1,'timeout':False} and row['native_accepted'] is (i==0)
  cases={'primary':PRIMARY.replace('.frame(','.'+space+'frame('),'opaque':OPAQUE.replace('.frame(','.'+space+'frame(')};assert row['cases']==cases
  assert row['baseline_configs']=={'primary':{'width':17,'height':9,'alphas':[4,2,8],'reverse':0},'opaque':{'color':'red','width':17,'height':9}}
  expected=('import SwiftUI\n'+''.join('let owned'+n+' = '+t+'\n' for n,t in cases.items())).encode();assert (e/f'control-{i}.swift').read_bytes()==expected
  assert (e/f'control-{i}.stdout').read_bytes()==b''
  diagnostic=(e/f'control-{i}.stderr').read_text()
  assert diagnostic=='' if i==0 else diagnostic.count("error: expected member name following '.'" if i==3 else "error: extraneous whitespace after '.' is not permitted")==2
  fixed=json.loads((e/'fixed/observations.json').read_text())[i];assert fixed['index']==i
  for name in ['primary','opaque']:
   f=fixed['results'][name];assert f['accepted'] is (i==0)
   if i==0:assert f['config']==row['baseline_configs'][name]
   else:assert f['error']=='Unsupported expression outside '+('primary-layer ZStack.frame' if name=='primary' else 'literal Color.frame')+' contract'
 assert json.loads((e/'assessment.json').read_text())['grammar_fix_warranted'] is True
 return {'compiler_processes':4,'accepted_expressions':2,'claim':'native syntax only'}
