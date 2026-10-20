"""Owned atomic signal and native source-selector controls; no workspace send."""
from pathlib import Path
import sys,subprocess,resource
root=Path('/Users/8amps/xcpreviewer-rs');source=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]).resolve();assert str(out).startswith(str(root/'research/raw')+'/') or str(out).startswith('/private/tmp/');out.mkdir(exist_ok=False,parents=True)
 clang='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
 for name,file in [('oracle','signal.m'),('probe','probe.m'),('resolve','resolve.m')]:
  (out/file).write_bytes((source/file).read_bytes());p=subprocess.run([clang,'-Wall','-Wextra','-Werror','-fblocks',str(source/file),'-framework','Foundation','-o',str(out/name)],capture_output=True,timeout=30);(out/(name+'-build.log')).write_bytes(p.stdout+p.stderr);p.check_returncode()
  p=subprocess.run([str(out/name),str(out)] if name=='probe' else [str(out/name)],capture_output=True,timeout=5);(out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(source/'verify.py'),str(out)],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);(out/'verification.stderr').write_bytes(p.stderr);p.check_returncode();print(p.stdout.decode())
