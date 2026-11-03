#!/usr/bin/env python3
"""Run shipped native observer controls in a fresh owned directory, never in Xcode."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--include-negative-control',action='store_true',help='Intentionally trigger recursive-lock termination in one isolated owned process');a=p.parse_args()
source=Path(__file__).resolve().parent;root=Path(os.environ.get('XCPREVIEWER_ROOT',str(source.parents[2])))
assert (root/'research/state/controller.lock').exists(),'Set XCPREVIEWER_ROOT to the reconstruction repository'
a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
files=['native.swift','bridge.s','bridge.h','identity.c','run-native.py','verify.py','make-crash.py']
for n in files:shutil.copyfile(source/n,a.output/n)
runner=a.output/'run-native.py';runner.write_text(runner.read_text().replace("'/Users/8amps/xcpreviewer-rs/research/state/controller.lock'","os.environ['XCPREVIEWER_ROOT']+'/research/state/controller.lock'"))
env={**os.environ,'XCPREVIEWER_ROOT':str(root)};modes=['invalidate','cancel','owner-loss','drop-waiting-token','ordering','reentrant','inflight','race','cancel-next','add-during-dispatch','cancel-admitted','self-drop','self-cancel-drop','invalidate-deinit-reentry','invalidate-deinit-add','late-while-blocked']
if a.include_negative_control:modes.append('cancel-reentry')
subprocess.run([sys.executable,str(runner),*modes],check=True,env=env,timeout=150)
if a.include_negative_control:subprocess.run([sys.executable,str(a.output/'make-crash.py')],check=True,env=env,timeout=10)
checked=subprocess.run([sys.executable,str(a.output/'verify.py'),str(a.output),*(['--negative'] if a.include_negative_control else [])],check=True,env=env,timeout=10,capture_output=True,text=True)
verified=json.loads(checked.stdout);assert set(verified)==set(modes),'Verifier omitted an executed control';print(checked.stdout,end='')
receipt={'classification':'native_component_execution','normal_controls':len(modes)-int(a.include_negative_control),'negative_control':a.include_negative_control,'full_canvas_parity':False,'source_sha256':{n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in files}}
(a.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
