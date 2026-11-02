from pathlib import Path
import os,sys,subprocess,fcntl,signal,time,json
root=Path(sys.argv[1])
with open(Path(os.environ.get('XCPREVIEWER_ROOT',str(Path(__file__).resolve().parents[3])))/'research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for mode in ['policy-log-unfulfilled','policy-log-fulfilled']:
  env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')};env['XCPREVIEWER_POLICY_GATE']='1'
  p=subprocess.Popen([str(root/'native'),mode],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  time.sleep(.3)
  try:out,err=p.communicate(input=b'\n',timeout=8);timeout=False
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate();timeout=True
  prefix=root/('gated-'+mode);prefix.with_suffix('.stdout').write_bytes(out);prefix.with_suffix('.stderr').write_bytes(err)
  prefix.with_suffix('.result.json').write_text(json.dumps({'pid':p.pid,'code':p.returncode,'timeout':timeout,'frida_attached':False},indent=2)+'\n')
  assert p.returncode==0 and not timeout and b'policy-ready-for-hooks' in out and json.loads(out.splitlines()[-1])['event']=='pass'
