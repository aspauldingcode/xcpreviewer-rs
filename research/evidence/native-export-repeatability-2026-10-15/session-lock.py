import sys,time,json,hashlib,subprocess
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
root=r/'research/build/preview-workspaces/preview-2b3aaa1663864b3fa200cd0eed456444'
with Controller().lock():
 assert hashlib.sha256((root/'Sources/PreviewLab/PreviewLab.swift').read_bytes()).hexdigest()=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
 Path('/private/tmp/owned-xcode-session-active').write_text('lock acquired\n')
 subprocess.run(['/usr/bin/open',str(root/'PreviewLab.xcodeproj')],check=True,timeout=5)
 deadline=time.monotonic()+85
 while time.monotonic()<deadline:
  if Path('/private/tmp/owned-xcode-session-done').exists():break
  time.sleep(.25)
 print(json.dumps({'lock_released':True,'completion_marker':Path('/private/tmp/owned-xcode-session-done').exists()}))
