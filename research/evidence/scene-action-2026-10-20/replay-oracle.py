"""Run an owned scene-action metadata/copy probe; no actions are sent.
Temporarily substitutes the base Objective-C initializer after runtime layout
and type checks; restores it immediately. Native Swift initializer is a trap.
"""
from pathlib import Path
import sys,subprocess,resource,json
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 raw=Path(sys.argv[1]).resolve();assert str(raw).startswith('/private/tmp/') or str(raw).startswith(str(r/'research/raw')+'/');raw.mkdir(parents=True,exist_ok=False);(raw/'oracle.m').write_text((w/'oracle.m').read_text());t='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/'
 for n,cmd in enumerate([[t+'clang','-Wall','-Wextra','-Werror',str(w/'oracle.m'),'-framework','Foundation','-o',str(raw/'oracle')],[str(raw/'oracle')]]):
  p=subprocess.run(cmd,cwd=raw,capture_output=True,timeout=30 if n==0 else 10);(raw/('oracle-%d.stdout'%n)).write_bytes(p.stdout);(raw/('oracle-%d.stderr'%n)).write_bytes(p.stderr);p.check_returncode()
 s=json.loads(p.stdout);assert s['uv_instance_size']==s['base_instance_size'] and s['extra_ivar_count']==0 and s['initializer_imp_restored']
 assert s['info_snapshot_frozen_after_source_mutation'] and s['payload_preserved'] and s['can_send_response_with_nil_responder'] is False
 assert [v['description'] for v in s['keys']]==[None,'messageType','payload','fenceHandle',None,None]
 print(json.dumps(s))
