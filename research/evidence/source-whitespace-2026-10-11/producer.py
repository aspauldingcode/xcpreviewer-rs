import pathlib,sys,json,subprocess,hashlib,shutil,datetime
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop import primarysource,viewsource
with Controller().lock():
 e=r/'research/evidence/source-whitespace-2026-10-11';e.mkdir();(e/'baseline').mkdir()
 texts={'primary':primarysource.expression(4),'opaque':'Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 17, height: 9)'}
 for n in ('primarysource','viewsource'):shutil.copyfile(r/f'tools/re/reloop/{n}.py',e/'baseline'/f'{n}.py')
 (e/'prediction.json').write_text(json.dumps({'scope':'Custom expression lowerers versus pinned native Swift frontend syntax only; no typecheck, renderer or Canvas claim','prediction':'Whitespace controls accepted by lowerers must parse as Swift; native disagreement falsifies lexical compatibility. Four bounded compiler invocations include normal whitespace, VT, FF, CR controls. No frame-byte claim.','limits':{'compiler_invocations':4,'each_seconds':10}},indent=2)+'\n')
 compiler=pathlib.Path('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swift-frontend');assert compiler.is_file()
 (e/'environment.json').write_text(json.dumps({'compiler_path':str(compiler),'compiler_sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r).decode().strip(),'bridge':'retained approved bridge offline; no restart/workspace opened'},indent=2)+'\n')
 rows=[]
 for i,(label,space) in enumerate([('normal',' '),('vertical-tab','\v'),('form-feed','\f'),('carriage-return','\r')]):
  cases={n:t.replace('Color(', 'Color'+space+'(') for n,t in texts.items()};p=e/f'control-{i}.swift';p.write_text('import SwiftUI\n'+''.join('let owned'+n+' = '+t+'\n' for n,t in cases.items()))
  accepted={n:getattr({'primary':primarysource,'opaque':viewsource}[n],'parse')(t) for n,t in cases.items()}
  try:x=subprocess.run([str(compiler),'-parse',str(p)],capture_output=True,timeout=10);code=x.returncode;timeout=False;stdout=x.stdout;stderr=x.stderr
  except subprocess.TimeoutExpired as x:code=None;timeout=True;stdout=x.stdout or b'';stderr=x.stderr or b''
  (e/f'control-{i}.stdout').write_bytes(stdout);(e/f'control-{i}.stderr').write_bytes(stderr)
  rows.append({'index':i,'label':label,'space_hex':space.encode().hex(),'cases':cases,'baseline_configs':accepted,'wait':{'code':code,'timeout':timeout},'native_accepted':code==0 and not timeout})
 (e/'observations.json').write_text(json.dumps(rows,indent=2)+'\n');print([{k:v for k,v in x.items() if k not in ('cases','baseline_configs')} for x in rows],flush=True)
