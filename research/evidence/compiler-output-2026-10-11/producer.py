import sys,pathlib,json,subprocess,resource,hashlib
from unittest.mock import patch
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop import sourcecache
with Controller().lock():
 e=r/'research/evidence/compiler-output-2026-10-11'
 emitter='''import os,sys,signal,resource,json,pathlib
signal.signal(signal.SIGXFSZ,signal.SIG_DFL)
pathlib.Path(sys.argv[2]).write_text(json.dumps({'file_limit':list(resource.getrlimit(resource.RLIMIT_FSIZE))}))
fd=1 if sys.argv[1]=='stdout' else 2
remaining=b'Z'*8192
while remaining:remaining=remaining[os.write(fd,remaining):]
'''
 (e/'emitter.py').write_text(emitter);realrun=subprocess.run
 for mode in ['baseline','fixed']:
  for stream in ['stdout','stderr']:
   root=e/mode/stream;root.mkdir(parents=True);args=[sys.executable,str(e/'emitter.py'),stream,str(root/'child.json')];before=list(resource.getrlimit(resource.RLIMIT_FSIZE));record={}
   def observed(*args,**kw):
    result=realrun(*args,**kw)
    for name in ['stdout','stderr']:
     f=kw[name];f.seek(0);record[name]=f.read(4097).hex()
    record.update(code=result.returncode,timeout=False,reaped=True);return result
   if mode=='baseline':
    result=realrun(args,capture_output=True,timeout=3);record={'code':result.returncode,'timeout':False,'reaped':True,'stdout':result.stdout.hex(),'stderr':result.stderr.hex(),'error':None}
   else:
    with patch.object(sourcecache.subprocess,'run',side_effect=observed):
     try:sourcecache.run_compiler(args,timeout=3,output_limit=4096)
     except RuntimeError as ex:record['error']=str(ex)
     else:raise AssertionError('Oversized compiler output accepted')
   after=list(resource.getrlimit(resource.RLIMIT_FSIZE));record.update(parent_limit_before=before,parent_limit_after=after);(root/'wait.json').write_text(json.dumps(record,indent=2)+'\n');print(mode,stream,record['code'],len(bytes.fromhex(record[stream])),flush=True)
 (e/'environment.json').write_text(json.dumps({'python':sys.version,'python_executable':sys.executable,'python_sha256':hashlib.sha256(pathlib.Path(sys.executable).resolve().read_bytes()).hexdigest(),'platform':sys.platform,'scope':'POSIX child-only resource limit; no Apple runtime/real compilation claim'},indent=2)+'\n')
