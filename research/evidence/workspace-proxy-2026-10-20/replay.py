from pathlib import Path
import subprocess,sys,resource
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
 for name in ['metadata','interface']:
  p=subprocess.run(['/usr/bin/clang','-Wall','-Wextra','-Werror',str(w/(name+'.m')),'-framework','Foundation','-o',str(out/name)],capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
  p=subprocess.run([str(out/name)],capture_output=True,timeout=5);(out/(name+'.json')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(w/'verify.py'),str(out/'interface.json')],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);p.check_returncode();print(p.stdout.decode())
