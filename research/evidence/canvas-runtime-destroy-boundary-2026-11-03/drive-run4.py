from pathlib import Path
import subprocess,time,json,sys
root=Path('/Users/8amps/xcpreviewer-rs');out=Path('/private/tmp/canvas-destroy-flow-20261103/run4')
p=subprocess.Popen([sys.executable,str(root/'tools/re/native-canvas-destroy-flow-runtime/session.py'),'--output',str(out),'--pid','45749','--source',str(root/'research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/Sources/PreviewLab/PreviewLab.swift')],cwd=root)
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
 print('Native owner returns observed after edit and restoration',flush=True)
finally:
 (out/'restore').touch();(out/'stop').touch();p.wait(timeout=15)
