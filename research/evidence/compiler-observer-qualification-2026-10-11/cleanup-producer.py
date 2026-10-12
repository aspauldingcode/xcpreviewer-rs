import sys,pathlib,json,time,hashlib,subprocess
from unittest.mock import patch
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 e=r/'research/evidence/compiler-observer-qualification-2026-10-11';assert (e/'detached/child-finished.json').exists();(e/'failed-producer.py').write_bytes(pathlib.Path('/private/tmp/observed-qualification-run.py').read_bytes());(e/'retained-failure.json').write_text(json.dumps({'observer_error':'OSError: Cannot observe a live owned root','cleanup_error':'PermissionError: [Errno 1] Operation not permitted','native_post_root_observer_qualified':False,'cold_build_attempted':False,'producer_retry':False,'spent_root_roles':2,'finite_child_finished':True},indent=2)+'\n')
 p=r/'tools/re/reloop/sourcecache.py';s=p.read_text();(e/'sourcecache-before-cleanup.py').write_text(s)
 old='''        except BaseException:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait(timeout=2)
            raise
''';new='''        except BaseException as failure:
            cleanup_errors=[]
            try:
                if process.poll() is None:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            except OSError as error:cleanup_errors.append('group_signal: '+repr(error))
            try:process.wait(timeout=2)
            except (OSError,subprocess.TimeoutExpired) as error:cleanup_errors.append('root_wait: '+repr(error))
            if cleanup_errors:
                try:failure.compiler_cleanup_errors=tuple(cleanup_errors)
                except Exception:pass
            raise
''';assert old in s;p.write_text(s.replace(old,new));(e/'sourcecache-after-cleanup.py').write_bytes(p.read_bytes());(e/'compilerwitness.py').write_bytes((r/'tools/re/reloop/compilerwitness.py').read_bytes())
 from reloop import sourcecache
 realpopen=subprocess.Popen;processes=[];attempts=[]
 def spawned(args,**kwargs):
  process=realpopen(args,**kwargs);processes.append(process);return process
 def observer(roots,known):
  if roots:raise RuntimeError('Owned observer unavailable control')
  return {}
 def denied(pid,sig):attempts.append({'pid':pid,'signal':sig,'injected_permission_error':True});raise PermissionError(1,'Owned signal denied control')
 folder=e/'denied-control';folder.mkdir();marker=folder/'finished.bin';source="import time,pathlib;time.sleep(0.2);pathlib.Path(%r).write_bytes(b'finished')" % str(marker);start=time.monotonic();failure=None
 with patch.object(sourcecache.subprocess,'Popen',side_effect=spawned),patch.object(sourcecache.os,'killpg',side_effect=denied):
  try:sourcecache.run_compiler([sys.executable,'-c',source],timeout=3,observer=observer)
  except RuntimeError as error:failure={'type':type(error).__name__,'message':str(error),'cleanup_errors':getattr(error,'compiler_cleanup_errors',())}
 (folder/'result.json').write_text(json.dumps({'failure':failure,'root_pid':processes[0].pid,'root_exit_code':processes[0].returncode,'elapsed_seconds':time.monotonic()-start,'attempts':attempts,'actual_signal_sent':False,'marker_bytes':marker.stat().st_size},indent=2)+'\n');print('denied',failure,'root',processes[0].returncode,flush=True)
 result=sourcecache.run_compiler([sys.executable,'-c','print("owned clean root")'],timeout=3);(e/'plain.json').write_text(json.dumps({'code':result.returncode,'stdout':result.stdout.decode(),'stderr':result.stderr.decode()},indent=2)+'\n')
 (e/'environment.json').write_text(json.dumps({'python':sys.executable,'python_sha256':hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest(),'observer_binary_sha256':hashlib.sha256((r/'research/build/libproc-observer-aa9cd15f087d41ad8f7bbe00c4162499/owned-process-snapshot').read_bytes()).hexdigest(),'scope':'Native observer failure retained; controlled permission-error branch qualification is independent and source-injected','total_root_roles':4},indent=2)+'\n')
 p=r/'tools/re/tests/test_compiler_observed_admission.py';s=p.read_text();old="for filename in ['sourcecache','compilerwitness']:self.assertEqual((ROOT/'tools/re/reloop'/f'{filename}.py').read_bytes(),(e/('sourcecache-after.py' if filename=='sourcecache' else 'compilerwitness.py')).read_bytes())";assert old in s;cache=r/'research/evidence/compiler-observed-admission-2026-10-11/sourcecache-after.py';witness=r/'research/evidence/compiler-observed-admission-2026-10-11/compilerwitness.py';new="for filename,digest in "+repr([(cache.name,hashlib.sha256(cache.read_bytes()).hexdigest()),(witness.name,hashlib.sha256(witness.read_bytes()).hexdigest())])+":self.assertEqual(hashlib.sha256((e/filename).read_bytes()).hexdigest(),digest)";p.write_text(s.replace(old,new))
