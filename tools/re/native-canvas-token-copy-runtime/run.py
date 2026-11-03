"""Run owned ABI qualification first, then native token-copy modes, without accessing Xcode processes."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
from verify import verify
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(exist_ok=False,parents=True);src=Path(__file__).resolve().parent
files=['native.swift','bridge.s','bridge.h','identity.c','run-native.py','verify.py','run.py']
for n in files:shutil.copyfile(src/n,out/n)
def run(args,timeout):
 r=subprocess.run([sys.executable,str(out/'run-native.py')]+args,capture_output=True,text=True,timeout=timeout)
 label='abi' if 'owned-copy-abi' in args else 'copies';(out/(label+'-runner.stdout')).write_text(r.stdout);(out/(label+'-runner.stderr')).write_text(r.stderr);print(r.stdout,end='',flush=True)
 if r.returncode:raise RuntimeError(label+' runner failed; native cases stop here')
run(['owned-copy-abi'],100)
run(['--no-build','copy-invalidate','copy-cancel','copy-drop-both','copy-owner-loss','copy-inflight'],50)
result=verify(out);(out/'assertions.json').write_text(json.dumps(result,indent=2)+'\n');(out/'source-hashes.json').write_text(json.dumps({n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in files},indent=2)+'\n');print(json.dumps(result))
