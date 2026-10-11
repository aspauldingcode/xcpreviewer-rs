import pathlib,sys,json,subprocess,os
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 e=r/'research/evidence/cache-input-2026-10-11';mode=sys.argv[1];module=e/'baseline/sourcecache.py' if mode=='baseline' else r/'tools/re/reloop/sourcecache.py'
 for kind in (['index'] if mode=='baseline' else ['index','manifest']):
  root=e/mode/kind
  p=subprocess.Popen([sys.executable,str(r/'tools/re/tests/cache_input_control.py'),str(module),str(root),kind],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,PYTHONPATH=str(r/'tools/re')));pid=p.pid
  try:
   try:stdout,stderr=p.communicate(timeout=2);timeout=False
   except subprocess.TimeoutExpired:p.kill();stdout,stderr=p.communicate(timeout=2);timeout=True
   (root/'wait.json').write_text(json.dumps({'pid':pid,'code':p.returncode,'timeout':timeout,'reaped':p.poll() is not None,'stdout':stdout.decode(),'stderr':stderr.decode()},indent=2)+'\n')
   bad=pathlib.Path(json.loads((root/'before.json').read_text())['bad_path']);bad.unlink();print(kind,p.returncode,timeout,flush=True)
  finally:
   if p.poll() is None:p.kill();p.wait(timeout=2)
   p.stdout.close();p.stderr.close()
