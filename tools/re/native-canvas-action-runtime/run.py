from pathlib import Path
import argparse,shutil,subprocess,sys,os,json,hashlib
p=argparse.ArgumentParser(description='Run actual native failure-action callback/lifetime controls in owned processes');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
source=Path(__file__).resolve().parent;root=Path(os.environ.get('XCPREVIEWER_ROOT',str(source.parents[2])));a.output=a.output.resolve();a.output.mkdir(exist_ok=False,parents=True)
files=['native.swift','bridge.s','bridge.h','identity.c','run-native.py','verify.py']
for n in files:shutil.copy2(source/n,a.output/n)
f=a.output/'run-native.py';f.write_text(f.read_text().replace("'/Users/8amps/xcpreviewer-rs/research/state/controller.lock'","os.environ['XCPREVIEWER_ROOT']+'/research/state/controller.lock'"))
env={**os.environ,'XCPREVIEWER_ROOT':str(root)}
modes=['action-unfulfilled-main','action-fulfilled-main','action-unfulfilled-worker','action-fulfilled-worker']
subprocess.run([sys.executable,str(f),*modes],env=env,check=True,timeout=150)
subprocess.run([sys.executable,str(a.output/'verify.py'),str(a.output)],env=env,check=True,timeout=10)
(a.output/'receipt.json').write_text(json.dumps({'classification':'actual native failure-action and capture lifetime execution','modes':modes,'source_sha256':{n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in files},'full_canvas_parity':False},indent=2)+'\n')
