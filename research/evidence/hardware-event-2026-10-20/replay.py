"""Replay in a fresh local folder with existing Apple tools; no event posting.
Compiler30s, each oracle10s, each validator2s; crashes are retained. Run under
an exclusive Controller lock. Raw event bytes and binaries must remain local.
"""
from pathlib import Path
import sys,subprocess,resource,json
from validator import validate
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
src=Path(__file__).resolve().parent;out=Path(sys.argv[1]).resolve()
assert str(out).startswith('/private/tmp/') or '/research/raw/' in str(out)
out.mkdir(parents=True,exist_ok=False)
clang='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
for name in ['oracle','worker']:
 p=subprocess.run([clang,'-Wall','-Wextra','-Werror',str(src/(name+'.m')),'-framework','Foundation','-framework','CoreGraphics','-o',str(out/name)],capture_output=True,timeout=30);(out/(name+'-build.log')).write_bytes(p.stdout+p.stderr);p.check_returncode()
for mode in ['valid','empty','text','truncated-public','truncated-private']:
 p=subprocess.run([str(out/'oracle'),str(out),mode],capture_output=True,timeout=10);(out/(mode+'.stdout')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr)
 assert p.returncode==(-11 if mode.startswith('truncated') else 0)
summary=json.loads((out/'valid.stdout').read_text());assert [v['bytes'] for v in summary['events']]==[260,212,260] and all(v['all_bytes_equal'] for v in summary['events'])
for n,t in enumerate([1,10,22]):
 v=validate(out/'worker',out/('event-%d.bin'%n));assert v=={'accepted':True,'type':t,'timestamp':123456789,'flags':131072,'status':'accepted'}
print(json.dumps({'native_event_bytes':732,'valid_events':3,'malformed_crash_isolated':True,'event_posted':False}))
