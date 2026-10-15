import sys,json,time,subprocess,uuid,os
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
root=Path(sys.argv[1]);state=Path(sys.argv[2]);state.mkdir(exist_ok=True)
lease_id=str(uuid.uuid4())
with Controller().lock():
 (state/'lease.json').write_text(json.dumps({'id':lease_id,'owned_root':str(root),'baseline_workspace_paths':[],'baseline_provenance':'Calling chat actual native XcodeListWindows returned No workspace windows found immediately before open','deadline_seconds':120})+'\n')
 subprocess.run(['/usr/bin/open',str(root/'PreviewLab.xcodeproj')],check=True,timeout=5)
 deadline=time.monotonic()+120;accepted=False
 while time.monotonic()<deadline:
  receipt=state/'release.json'
  if receipt.exists():
   v=json.loads(receipt.read_text())
   if v.get('lease_id')==lease_id and v.get('native_message')=='No workspace windows found' and v.get('source')=='actual_mcp__xcode__XcodeListWindows':accepted=True;break
   raise RuntimeError('Invalid or nonempty release inventory; lock not admitted for release')
  time.sleep(.2)
 result={'lease_id':lease_id,'verified_empty_release_receipt':accepted,'scope':'Calling-chat native MCP receipt binding, not cryptographic server attestation','deadline_expired':not accepted}
 (state/'lease-result.json').write_text(json.dumps(result)+'\n');print(json.dumps(result));assert accepted
