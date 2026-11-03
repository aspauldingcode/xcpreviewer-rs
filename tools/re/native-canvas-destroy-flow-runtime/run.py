"""Drive real file edits for bounded owner/interior native observations."""
from pathlib import Path
import subprocess,time,json,sys
import argparse,os
a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--source',type=Path,required=True);a.add_argument('--pid',type=int,required=True);a=a.parse_args()
root=Path(os.environ.get('XCPREVIEWER_ROOT',str(Path(__file__).resolve().parents[3])));out=a.output.resolve();assert not out.exists()
p=subprocess.Popen([sys.executable,str(root/'tools/re/native-canvas-destroy-flow-runtime/session.py'),'--output',str(out),'--pid',str(a.pid),'--source',str(a.source.resolve())],cwd=root)
def wait(check,seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if check():return
  if p.poll() is not None:raise RuntimeError('session exited')
  time.sleep(.1)
 raise TimeoutError('phase deadline')
def events():
 if not (out/'events.jsonl').exists():return []
 return [json.loads(x).get('message',{}).get('payload',{}) for x in (out/'events.jsonl').read_text().splitlines() if x.endswith('}')]
try:
 wait(lambda:(out/'ready').exists(),20)
 time.sleep(1)
 (out/'edit').touch();wait(lambda:(out/'edited').exists(),5)
 wait(lambda:any(x.get('event')=='owner-return' and x.get('phase')=='edit' for x in events()),25)
 (out/'restore').touch();wait(lambda:(out/'restored').exists(),5)
 wait(lambda:any(x.get('event')=='owner-return' and x.get('phase')=='restore' for x in events()),25)
finally:
 if out.exists():(out/'restore').touch();(out/'stop').touch()
 p.wait(timeout=15)
if p.returncode!=0:raise RuntimeError('native helper failed')
rows=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
if rows[-1].get('stage')!='session-ended-no-target-termination' or not rows[-1].get('source_restored'):raise RuntimeError('source restoration not confirmed')
print('Native owner returns observed; helper exited zero and source restored',flush=True)
