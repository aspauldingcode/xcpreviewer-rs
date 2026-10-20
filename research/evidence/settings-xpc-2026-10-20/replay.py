"""Fresh owned native serializer/decoder replay under exclusive controller lock."""
from pathlib import Path
import sys,subprocess,resource,shutil,json
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]).resolve();assert str(out).startswith(str(r/'research/raw')+'/') or str(out).startswith('/private/tmp/');out.mkdir(exist_ok=False,parents=True)
 for name in ['oracle','metadata']:
  shutil.copyfile(w/(name+'.m'),out/(name+'.m'));p=subprocess.run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(out/(name+'.m')),'-framework','Foundation','-o',str(out/name)],capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
  p=subprocess.run([str(out/name)],capture_output=True,timeout=5);(out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(w/'verify.py'),str(out/'oracle.stdout')],capture_output=True,timeout=10);p.check_returncode();(out/'verification.json').write_bytes(p.stdout);print(p.stdout.decode())
