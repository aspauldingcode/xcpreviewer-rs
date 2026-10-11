import sys,pathlib,json,hashlib,shutil,subprocess
from unittest.mock import patch
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.portablelayers import RUN,ANCHOR
from reloop.portable import TOOLCHAIN
from reloop.primarysource import expression
from reloop import sourcecache
with Controller().lock():
 c=Controller();v=c.verify(RUN,ANCHOR);assert v['valid'] and v['external_anchor_matches']
 e=r/'research/evidence/capped-build-2026-10-11';e.mkdir();(e/'native-anchor.json').write_text(json.dumps({'run':RUN,'anchor':ANCHOR,'valid':v['valid'],'external_anchor_matches':v['external_anchor_matches']},indent=2)+'\n')
 native=(c.runs/RUN/'output/layers-4-forward-0.0.raw').read_bytes();assert native==(bytes([96,64,95,255])*17+bytes([165])*12)*9;(e/'native-callback.raw').write_bytes(native)
 (e/'prediction.json').write_text(json.dumps({'scope':'Current capped real LLVM sourcecache cold build/cache hit, V8 full allocations and WasmKit render return; macOS only','config':{'width':17,'height':9,'alphas':[4,2,8],'reverse':0},'pixel':[96,64,95,255],'strides':[68,80],'allocation_bytes':16384,'native_prefix_bytes':720,'tail_byte':195,'padding_byte':165,'limits':{'producers':4,'compiler_seconds':30,'compiler_file_bytes':4194304,'runtime_seconds':15}},indent=2)+'\n')
 text=expression(4);(e/'input.swift').write_text(text);realrun=subprocess.run;calls=[]
 def observed(args,**kw):
  result=realrun(args,**kw);row={'argv':args,'code':result.returncode,'timeout':False,'timeout_seconds':kw['timeout'],'preexec_present':callable(kw.get('preexec_fn'))}
  for n in ['stdout','stderr']:
   file=kw[n];file.seek(0);row[n]=file.read(4194305).hex()
  calls.append(row);return result
 with patch.object(sourcecache.subprocess,'run',side_effect=observed):
  cold=sourcecache.build(text,e/'cache',e/'output',TOOLCHAIN/'clang',TOOLCHAIN/'wasm-ld');before=(e/'output/current.json').read_bytes();hit=sourcecache.build(text,e/'cache',e/'output',TOOLCHAIN/'clang',TOOLCHAIN/'wasm-ld');assert (e/'output/current.json').read_bytes()==before and len(calls)==2
 (e/'build.json').write_text(json.dumps({'cold':cold,'hit':hit,'calls':calls,'pointer_hex':before.hex()},indent=2)+'\n')
 module=e/'output'/cold['module'];(e/'jobs.json').write_text(json.dumps([{'index':0,'module':str(module),'config':cold['config'],'strides':[68,80]}]))
 shutil.copyfile(r/'tools/re/reloop/primary_source_runner.js',e/'runner.js')
 node=pathlib.Path(shutil.which('node'));wasmkit=TOOLCHAIN/'wasmkit'
 for name,args in [('v8',[str(node),str(e/'runner.js'),str(e)]),('wasmkit',[str(wasmkit),'run',str(module),'render','i32:80'])]:
  result=realrun(args,capture_output=True,timeout=15);(e/(name+'-wait.json')).write_text(json.dumps({'argv':args,'code':result.returncode,'timeout':False,'stdout':result.stdout.decode(),'stderr':result.stderr.decode()},indent=2)+'\n');print(name,result.returncode,result.stdout.decode()[:100],flush=True);result.check_returncode()
 (e/'environment.json').write_text(json.dumps({'tools':{name:{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for name,path in [('clang',TOOLCHAIN/'clang'),('wasm_ld',TOOLCHAIN/'wasm-ld'),('node',node),('wasmkit',wasmkit)]},'python':sys.version,'platform':sys.platform},indent=2)+'\n');shutil.copyfile(r/'tools/re/reloop/sourcecache.py',e/'sourcecache.py')
 print('module',cold['module_sha256'],'cold/hit',cold['cache_hit'],hit['cache_hit'])
