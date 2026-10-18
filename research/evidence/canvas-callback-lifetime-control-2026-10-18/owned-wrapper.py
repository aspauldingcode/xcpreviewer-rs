"""Owned experiment adapter; keep the observed root alive across fast child exit."""
import sys,subprocess,json,time,os
# Bound child wait independently from the controller's wrapper wait.
probe,root,mode=sys.argv[1:]
started=time.monotonic()
child=subprocess.Popen([probe,root,mode],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
 out,err=child.communicate(timeout=2)
except subprocess.TimeoutExpired:
 child.kill();out,err=child.communicate(timeout=1)
 print(json.dumps({'child_pid':child.pid,'child_wait':child.returncode,'timed_out':True}),flush=True)
 sys.exit(3)
print(json.dumps({'child_pid':child.pid,'child_wait':child.returncode,'timed_out':False,'stdout_hex':out.hex(),'stderr_hex':err.hex(),'wrapper_pid':os.getpid(),'hold_seconds':1,'elapsed_before_hold':time.monotonic()-started}),flush=True)
time.sleep(1)
sys.exit(0)
