"""Bounded local responder factory/queue/deadline controls; no external transport or Swift ABI calls."""
from pathlib import Path
import sys,subprocess,resource
root=Path('/Users/8amps/xcpreviewer-rs');source=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]).resolve();assert str(out).startswith(str(root/'research/raw')+'/') or str(out).startswith('/private/tmp/')
 out.mkdir(exist_ok=False,parents=True);(out/'oracle.m').write_bytes((source/'oracle.m').read_bytes())
 cmd=['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(source/'oracle.m'),'-framework','Foundation','-o',str(out/'oracle')]
 p=subprocess.run(cmd,capture_output=True,timeout=30);(out/'build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
 for mode in ['factory-error','both-fields','deadline']:
  p=subprocess.run([str(out/'oracle'),mode],cwd=out,capture_output=True,timeout=5);(out/(mode+'.stdout')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(source/'verify.py'),str(out)],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);(out/'verification.stderr').write_bytes(p.stderr);p.check_returncode();print(p.stdout.decode())
