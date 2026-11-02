import fcntl,time,hashlib,json
from pathlib import Path
r=Path(__file__).parent/'ui-body';s=Path('/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/Sources/PreviewLab/PreviewLab.swift')
before=s.read_bytes();r.joinpath('PreviewLab.before.swift').write_bytes(before);after=before.replace(b'Canvas baseline',b'Runtime edit A').replace(b'#Preview("Layout edit"',b'#Preview("Runtime edit A"');after=after.replace(b'Layout baseline',b'Runtime pixels A');assert after!=before
for n in ['ui-stop','ui-edit','ui-edited','ui-restore','ui-restored']:r.joinpath(n).unlink(missing_ok=True)
def event(e,**kw):
 with (r/'ui-session.jsonl').open('a') as f:f.write(json.dumps({'event':e,'time_ns':time.monotonic_ns(),**kw})+'\n')
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);event('lock-acquired',source=str(s),before_sha256=hashlib.sha256(before).hexdigest());r.joinpath('ui-ready').touch();end=time.monotonic()+240;edited=False;restored=False
 try:
  while time.monotonic()<end and not r.joinpath('ui-stop').exists():
   if r.joinpath('ui-edit').exists() and not edited:
    assert s.read_bytes()==before,'concurrent source modification';s.write_bytes(after);edited=True;event('source-edited',sha256=hashlib.sha256(after).hexdigest());r.joinpath('ui-edited').touch()
   if r.joinpath('ui-restore').exists() and edited and not restored:
    assert s.read_bytes()==after,'concurrent source modification';s.write_bytes(before);restored=True;event('source-restored',sha256=hashlib.sha256(before).hexdigest());r.joinpath('ui-restored').touch()
   time.sleep(.1)
 finally:
  if edited and not restored:
   if s.read_bytes()==after:s.write_bytes(before);event('source-restored-finally')
   else:event('restore-skipped-user-edit')
  event('lock-released')
