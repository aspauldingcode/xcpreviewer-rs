import sys,pathlib,json,time,hashlib
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 p=r/'tools/re/reloop/sourcecache.py';s=p.read_text();old='        result=subprocess.CompletedProcess(args,code)\n';new='''        # Root success is insufficient while any member of its session group
        # remains. This read-only, fail-closed guard does not claim ownership
        # of a reused group, and never signals it. Escaped groups are separate.
        if code==0:
            try:os.killpg(process.pid,0)
            except ProcessLookupError:pass
            else:raise RuntimeError('Compiler process group remains after successful root exit')
        result=subprocess.CompletedProcess(args,code)
''';assert old in s;p.write_text(s.replace(old,new))
 e=r/'research/evidence/compiler-success-admission-2026-10-11';e.mkdir();(e/'sourcecache-before.py').write_text(s);(e/'sourcecache-after.py').write_bytes(p.read_bytes())
 emitter=(r/'tools/re/fixtures/CompilerSuccessDescendant/emitter.py').read_text().replace("print(json.dumps({'pid':os.getpid(),'child_pid':child,'process_group':os.getpgrp(),'owns_child':True}),flush=True)", "row={'pid':os.getpid(),'child_pid':child,'process_group':os.getpgrp(),'owns_child':True};(folder/'root.json').write_text(json.dumps(row)+'\\n');print(json.dumps(row),flush=True)")
 f=r/'tools/re/fixtures/CompilerSuccessAdmission';f.mkdir();(f/'emitter.py').write_text(emitter);(e/'emitter.py').write_text(emitter)
 (e/'prediction.json').write_text(json.dumps({'scope':'Conservative success admission: process group presence after root0 rejects before build caller accepts completion; no new termination route','prediction':'Finite owned child surviving root0 triggers RuntimeError while plain Python and actual Xcode clang object compile pass when groups disappear. Existing group is observed with signal0 only; no claim about escaped descendants or false-positive reused/zombie groups.','limits':{'producer_processes':4,'compiler_deadline_seconds':3,'clang_deadline_seconds':10,'child_ticks':24,'child_tick_seconds':0.05,'finish_wait_seconds':3}},indent=2)+'\n')
 from reloop.sourcecache import run_compiler
 folder=e/'survivor';folder.mkdir();started=time.monotonic();error=None
 try:run_compiler([sys.executable,str(e/'emitter.py'),str(folder)],timeout=3)
 except RuntimeError as x:error=str(x)
 elapsed=time.monotonic()-started;first=(folder/'heartbeat.bin').read_bytes();(folder/'at-rejection.bin').write_bytes(first);time.sleep(0.3);later=(folder/'heartbeat.bin').read_bytes();(folder/'after-rejection.bin').write_bytes(later);end=time.monotonic()+3
 while not (folder/'child-finished.json').exists() and time.monotonic()<end:time.sleep(0.05)
 (folder/'result.json').write_text(json.dumps({'error':error,'elapsed_seconds':elapsed,'first_bytes':len(first),'later_bytes':len(later),'child_finished':(folder/'child-finished.json').exists(),'kill_signal_used':False},indent=2)+'\n');print('survivor',error,len(first),len(later),flush=True)
 plain=run_compiler([sys.executable,'-c','print("owned clean root")'],timeout=3);(e/'plain.json').write_text(json.dumps({'code':plain.returncode,'stdout':plain.stdout.decode(),'stderr':plain.stderr.decode()},indent=2)+'\n')
 compiler='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang';c=e/'owned.c';c.write_text('int owned_constant(void){return 7;}\n');obj=r/'research/build/success-admission.o';clang=run_compiler([compiler,'-c',str(c),'-o',str(obj)],timeout=10);(e/'clang.json').write_text(json.dumps({'code':clang.returncode,'stdout':clang.stdout.decode(),'stderr':clang.stderr.decode(),'compiler':compiler,'compiler_sha256':hashlib.sha256(pathlib.Path(compiler).read_bytes()).hexdigest(),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'object_bytes':obj.stat().st_size},indent=2)+'\n');print('plain',plain.returncode,'clang',clang.returncode,flush=True)
 (e/'environment.json').write_text(json.dumps({'python':sys.executable,'python_sha256':hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest(),'platform':sys.platform,'scope':'Owned source-level compiler process admission; not native Canvas or shipped Apple binary interpretation'},indent=2)+'\n')
