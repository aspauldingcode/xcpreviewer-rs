"""Native service-queue fallback/capture control, not a workspace transport test."""
from pathlib import Path
import sys,subprocess,resource
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]).resolve();assert str(out).startswith(str(r/'research/raw')+'/') or str(out).startswith('/private/tmp/');out.mkdir(exist_ok=False,parents=True);(out/'oracle.m').write_bytes((w/'oracle.m').read_bytes())
 p=subprocess.run(['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(w/'oracle.m'),'-framework','Foundation','-o',str(out/'oracle')],capture_output=True,timeout=30);(out/'build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
 for mode in ['early','fallback']:
  p=subprocess.run([str(out/'oracle'),mode],capture_output=True,timeout=3);(out/(mode+'.stdout')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(w/'verify.py'),str(out)],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);(out/'verification.stderr').write_bytes(p.stderr);p.check_returncode();print(p.stdout.decode())
