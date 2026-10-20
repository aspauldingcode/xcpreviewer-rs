from pathlib import Path
import subprocess,resource,json,hashlib,sys
w=Path(__file__).parent;out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
p=subprocess.run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-Wno-error=deprecated-declarations',str(w/'oracle.c'),'-lbsm','-o',str(out/'oracle')],capture_output=True,timeout=30);(out/'build.log').write_bytes(p.stderr);p.check_returncode()
for mode in ['clean','abrupt','no-send']:
 d=out/mode;d.mkdir();p=subprocess.run([str(out/'oracle'),mode,str(d)],capture_output=True,timeout=5);(d/'stdout.json').write_bytes(p.stdout);(d/'stderr.log').write_bytes(p.stderr);p.check_returncode();assert json.loads(p.stdout)['ok']
print(json.dumps({'native_cases':3,'out':str(out)}))
