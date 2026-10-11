"""Independent reader for four native parse-only lexical controls."""
import hashlib,json
from pathlib import Path
COMPILER_SHA='2ed38571e92c0283091838c1649e27650ad9c99950288e883c7b2dc6c4ce89fb'
PRIMARY='ZStack {\nColor(.sRGB, red: 0, green: 0, blue: 1, opacity: 1.0)\nColor(.sRGB, red: 1, green: 0, blue: 0, opacity: 0.5)\nColor(.sRGB, red: 0, green: 1, blue: 0, opacity: 0.25)\n}.frame(width: 17, height: 9)\n'
OPAQUE='Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 17, height: 9)'
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 env=json.loads((e/'environment.json').read_text());assert env['compiler_sha256']==COMPILER_SHA
 rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==COMPILER_SHA;assert rea['identity']['result']['path']==env['compiler_path'] and rea['identity']['result']['architecture']=='arm64';assert rea['closed']['result'] is None
 rows=json.loads((e/'observations.json').read_text());assert len(rows)==4
 for i,(row,(label,space)) in enumerate(zip(rows,[('normal',' '),('vertical-tab','\v'),('form-feed','\f'),('carriage-return','\r')])):
  assert row['index']==i and row['label']==label and row['space_hex']==space.encode().hex();assert row['wait']=={'code':0,'timeout':False} and row['native_accepted'] is True
  cases={'primary':PRIMARY.replace('Color(','Color'+space+'('),'opaque':OPAQUE.replace('Color(','Color'+space+'(')};assert row['cases']==cases
  assert row['baseline_configs']=={'primary':{'width':17,'height':9,'alphas':[4,2,8],'reverse':0},'opaque':{'color':'red','width':17,'height':9}}
  expected=('import SwiftUI\n'+''.join('let owned'+n+' = '+t+'\n' for n,t in cases.items())).encode();assert (e/f'control-{i}.swift').read_bytes()==expected
  assert (e/f'control-{i}.stdout').read_bytes()==(e/f'control-{i}.stderr').read_bytes()==b''
 assert json.loads((e/'assessment.json').read_text())['grammar_fix_warranted'] is False
 return {'compiler_processes':4,'accepted_expressions':8,'claim':'native syntax only'}
