from pathlib import Path
import subprocess,resource,sys
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
 p=subprocess.run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(w/'identity.m'),'-framework','Foundation','-o',str(out/'identity')],capture_output=True,timeout=30);(out/'build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
 p=subprocess.run([str(out/'identity')],capture_output=True,timeout=5);(out/'identity.json').write_bytes(p.stdout);(out/'stderr.log').write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(w/'verify.py'),str(out/'identity.json')],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);p.check_returncode();print(p.stdout.decode())
