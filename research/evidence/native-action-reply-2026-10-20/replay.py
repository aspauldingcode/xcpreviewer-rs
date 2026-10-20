"""Bounded owned BSAction reply/capture oracle. No external transport.
Run against this pinned native profile; callback counts and150ms observation do
not prove unbounded no-later-effect or remote target-operation settlement.
"""
from pathlib import Path
import sys,subprocess,resource,json
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 raw=Path(sys.argv[1]).resolve();assert str(raw).startswith('/private/tmp/') or str(raw).startswith(str(r/'research/raw')+'/');raw.mkdir(parents=True,exist_ok=False);(raw/'oracle.m').write_text((w/'oracle.m').read_text());clang='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
 p=subprocess.run([clang,'-Wall','-Wextra','-Werror','-fblocks',str(w/'oracle.m'),'-framework','Foundation','-o',str(raw/'oracle')],capture_output=True,timeout=30);(raw/'build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
 for mode in ['reply','error','timeout','invalidate']:
  p=subprocess.run([str(raw/'oracle'),mode],capture_output=True,cwd=raw,timeout=5);(raw/(mode+'.stdout')).write_bytes(p.stdout);(raw/(mode+'.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(w/'verify.py'),str(raw)],capture_output=True,timeout=10);(raw/'verification.json').write_bytes(p.stdout);(raw/'verification.stderr').write_bytes(p.stderr);p.check_returncode();print(p.stdout.decode())
