"""Finite research-only check of a future clean implementer process boundary.
Does not launch an implementer or export a target-derived specification.
"""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
from reloop.core import Controller
root=Path('/private/tmp/clean-isolation-control-v2-20261019')
with Controller().lock():
    root.mkdir(exist_ok=False); package=root/'package'; work=root/'work'; excluded=root/'excluded'
    for d in [package,work,excluded]: d.mkdir(mode=0o700)
    (package/'SPEC.txt').write_text('ORIGINAL CONTROL INPUT\n')
    (excluded/'CONTROL.txt').write_text('EXCLUDED CONTROL INPUT\n')
    (package/'escape.txt').symlink_to(excluded/'CONTROL.txt')
    profile='''(version 1)
(deny default)
(allow syscall*)
(allow mach-bootstrap)
(allow file-read-metadata)
(allow process-exec)
(allow process-fork)
(allow sysctl-read)
(allow file-read* (subpath "/System") (subpath "/usr/lib") (subpath "/bin") (subpath "/usr/bin") (literal "/dev/null") (subpath "PACKAGE") (subpath "WORK"))
(allow file-write* (literal "/dev/null") (subpath "WORK"))
'''.replace('PACKAGE',str(package)).replace('WORK',str(work))
    (root/'profile.sb').write_text(profile)
    plan={'scope':'Candidate subprocess file access boundary only, not model context/tool isolation or clean-room certification.','prediction':'Allow original package reads and output writes; reject excluded sibling/research reads, symlink escape and package mutation.','negative_control':'Unsandboxed owned excluded sentinel read must succeed.','limits':{'calls':7,'timeout_seconds_each':5,'whole_run_seconds':45},'product_or_agent_launched':False,'approved_spec_exported':False,'profile_sha256':hashlib.sha256(profile.encode()).hexdigest()}
    (root/'plan.json').write_text(json.dumps(plan,indent=2))
    started=time.monotonic(); results=[]
    cases=[('unsandboxed-control',['/bin/cat',str(excluded/'CONTROL.txt')],False),('allowed-input',['/bin/cat',str(package/'SPEC.txt')],True),('excluded-sibling',['/bin/cat',str(excluded/'CONTROL.txt')],True),('symlink-escape',['/bin/cat',str(package/'escape.txt')],True),('research-read',['/bin/cat','/Users/8amps/xcpreviewer-rs/Cargo.toml'],True),('allowed-write',['/bin/sh','-c','printf OUTPUT > "$1"','control',str(work/'result.txt')],True),('input-mutation',['/bin/sh','-c','printf CHANGED > "$1"','control',str(package/'SPEC.txt')],True)]
    for label,command,sandboxed in cases:
        if time.monotonic()-started>40: raise RuntimeError('fixed budget expired')
        args=['/usr/bin/sandbox-exec','-f',str(root/'profile.sb')]+command if sandboxed else command
        r=subprocess.run(args,cwd=work,capture_output=True,timeout=5,env={'PATH':'/usr/bin:/bin','HOME':str(work),'TMPDIR':str(work)})
        row={'case':label,'sandboxed':sandboxed,'exit':r.returncode,'stdout_bytes':len(r.stdout),'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr':r.stderr.decode(errors='replace')[:1500]}
        if label in ['unsandboxed-control','allowed-input']: row['stdout_matches_owned_sentinel']=r.stdout==(excluded/'CONTROL.txt' if label=='unsandboxed-control' else package/'SPEC.txt').read_bytes()
        results.append(row); (root/'results.json').write_text(json.dumps(results,indent=2))
        if sandboxed and b'sandbox_init' in r.stderr:
            print(json.dumps({'status':'sandbox_launch_unavailable','retained':str(root),'last_result':row})); sys.exit(3)
    expected={'unsandboxed-control':0,'allowed-input':0,'excluded-sibling':1,'symlink-escape':1,'research-read':1,'allowed-write':0,'input-mutation':1}
    failures=[r for r in results if (r['exit']==0)!=(expected[r['case']]==0)]
    intact=(package/'SPEC.txt').read_bytes()==b'ORIGINAL CONTROL INPUT\n'
    written=(work/'result.txt').read_bytes()==b'OUTPUT' if (work/'result.txt').exists() else False
    passed=not failures and intact and written and all(r.get('stdout_matches_owned_sentinel',True) for r in results)
    summary={'passed':passed,'cases':len(results),'input_intact':intact,'output_exact':written,'elapsed_seconds':time.monotonic()-started,'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_tool_isolation_proven':False,'handoff_approved':False}
    (root/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary))
    if not passed: sys.exit(2)
