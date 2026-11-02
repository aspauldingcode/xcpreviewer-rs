from pathlib import Path
import json,subprocess,sys,threading,queue,time,hashlib,os,signal
r=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent
source=w/'Source.swift';output=w/'frame.bplist';png=w/'reference.png'
a='import SwiftUI\nfunc makePreview() -> some View { Color.red }\n'
b='import SwiftUI\nfunc makePreview() -> some View { Color.blue }\n'
source.write_text(a)
command=[sys.executable,str(r/'tools/re/swiftui-preview/watch.py'),str(source),'--output',str(output),'--reference-png',str(png),'--width','32','--height','24','--interval','0.05','--debounce','0.1']
p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
lines=queue.Queue();events=[]
def pump():
 for line in p.stdout:lines.put(line)
threading.Thread(target=pump,daemon=True).start()
def wait(status):
 deadline=time.monotonic()+60
 while time.monotonic()<deadline:
  try:line=lines.get(timeout=min(1,max(.01,deadline-time.monotonic())))
  except queue.Empty:
   if p.poll() is not None:raise AssertionError(('watcher ended',p.returncode,p.stderr.read()))
   continue
  event=json.loads(line);events.append(event)
  if event['status']==status:return event
 raise AssertionError(('event deadline',status,events))
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
try:
 wait('capturing');source.write_text(b)
 wait('superseded');published=wait('published')
 good=(sha(output),sha(png));assert published['capture']['source_sha256']==hashlib.sha256(b.encode()).hexdigest()
 source.write_text('invalid swift source\n');wait('capture-error');assert good==(sha(output),sha(png))
 source.write_text(a);next_frame=wait('published');assert next_frame['capture']['source_sha256']==hashlib.sha256(a.encode()).hexdigest() and sha(output)!=good[0]
 p.send_signal(signal.SIGINT);p.wait(timeout=5);assert p.returncode==130
finally:
 if p.poll() is None:
  p.send_signal(signal.SIGINT)
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 (w/'watcher.stderr').write_text(p.stderr.read());(w/'events.json').write_text(json.dumps(events,indent=2)+'\n')
# Real interruption of only the helper process group created by each runner.
interrupts=[]
for module in ['capture','discover']:
 marker=w/(module+'.pid');marker.unlink(missing_ok=True)
 child='import os,time;from pathlib import Path;Path('+repr(str(marker))+').write_text(str(os.getpid()));time.sleep(30)'
 runner='import sys,os,json;sys.path.insert(0,'+repr(str(r/'tools/re/swiftui-preview'))+');import '+module+' as m\ntry:m.run([sys.executable,"-c",'+repr(child)+'],40,dict(os.environ))\nexcept KeyboardInterrupt:print("owned-interrupt-cleaned",flush=True)'
 parent=subprocess.Popen([sys.executable,'-c',runner],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 try:
  deadline=time.monotonic()+5
  while not marker.exists() and time.monotonic()<deadline:time.sleep(.02)
  assert marker.exists(),'Owned helper did not start'
  pid=int(marker.read_text());parent.send_signal(signal.SIGINT);out,err=parent.communicate(timeout=5)
  assert parent.returncode==0 and out.strip()==b'owned-interrupt-cleaned',(out,err)
  try:os.kill(pid,0)
  except ProcessLookupError:pass
  else:raise AssertionError('Owned helper survived interrupt')
  interrupts.append({'module':module,'owned_helper_reaped':True,'parent_caught_interrupt':True})
 finally:
  if parent.poll() is None:parent.kill();parent.wait()
(w/'results.json').write_text(json.dumps({'passed':True,'native_successful_captures':3,'superseded_not_published':1,'compiler_failure_preserved_payload_and_png':True,'successful_revision_changed_payload':True,'watcher_interrupt_exit':130,'real_interrupt_controls':interrupts,'scope':'Original source-watcher policy over the qualified Mac producer. No native Canvas session/state/provider parity or Rust test rerun.'},indent=2)+'\n')
print((w/'results.json').read_text())
