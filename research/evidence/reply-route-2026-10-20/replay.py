"""Bounded owned libxpc reply tracing; inject only an original owned helper."""
from pathlib import Path
import subprocess,sys,shutil,resource
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]).resolve();assert str(out).startswith(str(r/'research/raw')+'/') or str(out).startswith('/private/tmp/');out.mkdir(parents=True,exist_ok=False)
 for n in ['oracle.m','trace.c','trace.h']:shutil.copyfile(w/n,out/n)
 commands={'trace':['/usr/bin/clang','-Wall','-Wextra','-Werror','-dynamiclib',str(out/'trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(out/'libtrace.dylib')],'oracle':['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(out/'oracle.m'),'-framework','Foundation','-L'+str(out),'-ltrace','-Wl,-rpath,@executable_path','-o',str(out/'oracle')]}
 for name,cmd in commands.items():
  p=subprocess.run(cmd,capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
 for mode in ['positive','native','native-changed','baseline']:
  p=subprocess.run([str(out/'oracle'),mode],capture_output=True,timeout=5);(out/(mode+'.stdout')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(w/'verify.py'),str(out)],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);(out/'verification.stderr').write_bytes(p.stderr);p.check_returncode();print(p.stdout.decode())
