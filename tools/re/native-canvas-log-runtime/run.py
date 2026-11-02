from pathlib import Path
import os,shutil,subprocess,sys,argparse,json,hashlib
p=argparse.ArgumentParser(description='Construct qualified log(String) inputs and observe owned native logging API calls');p.add_argument('--output',type=Path,required=True);p.add_argument('--query-log-store',action='store_true');a=p.parse_args()
source=Path(__file__).resolve().parent;root=Path(os.environ.get('XCPREVIEWER_ROOT',str(source.parents[2])));a.output=a.output.resolve();a.output.mkdir(exist_ok=False,parents=True)
files=['native.swift','bridge.s','bridge.h','identity.c','run-native.py','trace.py','agent.js','qualify.py','verify.py','nohooks.py','store.py']
for n in files:shutil.copy2(source/n,a.output/n)
shutil.copy2(root/'research/evidence/canvas-failure-policy-2026-11-02/macho.py',a.output/'macho.py')
f=a.output/'run-native.py';f.write_text(f.read_text().replace("'/Users/8amps/xcpreviewer-rs/research/state/controller.lock'","os.environ['XCPREVIEWER_ROOT']+'/research/state/controller.lock'"))
env={**os.environ,'XCPREVIEWER_ROOT':str(root)}
r=subprocess.run([sys.executable,str(a.output/'qualify.py')],env=env,capture_output=True,timeout=5,check=True);(a.output/'qualification.json').write_bytes(r.stdout)
subprocess.run([sys.executable,str(f),'policy-log-unfulfilled','policy-log-fulfilled'],env=env,check=True,timeout=130)
subprocess.run([sys.executable,str(a.output/'trace.py')],env=env,check=True,timeout=90)
subprocess.run([sys.executable,str(a.output/'nohooks.py'),str(a.output)],env=env,check=True,timeout=30)
if a.query_log_store:subprocess.run([sys.executable,str(a.output/'store.py'),str(a.output)],env=env,check=True,timeout=30)
subprocess.run([sys.executable,str(a.output/'verify.py'),str(a.output),*(['--store'] if a.query_log_store else [])],env=env,check=True,timeout=10)
(a.output/'receipt.json').write_text(json.dumps({'classification':'owned native log policy and logging API observation','source_sha256':{n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in files},'user_xcode_accessed':False,'os_log_persistence_verified':a.query_log_store,'full_canvas_parity':False},indent=2)+'\n')
