from pathlib import Path
import subprocess
w=Path(__file__).parent
for name,args in [('trace',['xcrun','clang','-Wall','-Wextra','-Werror','-dynamiclib',str(w/'OwnedSendTrace.c'),'-install_name','@rpath/libOwnedSendTrace.dylib','-o',str(w/'libOwnedSendTrace.dylib')]),('probe',['xcrun','clang','-fno-objc-arc','-fblocks','-framework','Foundation',str(w/'probe.m'),'-L'+str(w),'-lOwnedSendTrace','-Wl,-rpath,@executable_path','-o',str(w/'probe')])]:
 p=subprocess.run(args,capture_output=True,timeout=30);(w/(name+'-build.stdout')).write_bytes(p.stdout);(w/(name+'-build.stderr')).write_bytes(p.stderr)
 if p.returncode:print(p.stderr.decode())
 p.check_returncode()
