import contextlib
import datetime
import fcntl
import hashlib
import json
import os
import pathlib
import re
import signal
import subprocess
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[3]
PROJECT_ROOT = pathlib.Path(os.environ.get('RE_PROJECT_ROOT', str(ROOT))).resolve()
ADAPTERS = {'surface_payload', 'portable_solid', 'inventory', 'runtime', 'disassembly', 'ghidra', 'ghidra_mcp', 'lldb_smoke', 'frida_smoke', 'native_reference', 'connected_probe', 'plist_corpus', 'swift_metadata', 'xcode_preview', 'xpc_corpus', 'xpc_negative', 'xpc_prefix', 'agent_discriminants', 'raw_coder', 'surface_corpus', 'preview_hook_smoke', 'surface_ipc', 'surface_failure', 'surface_reuse', 'xcode_bridge_probe'}
PARAMS = {
    'surface_payload': {'payload'},
    'portable_solid': {'second_runtime'},
    'inventory': {'xcode'}, 'runtime': {'xcode'}, 'disassembly': {'binary', 'query','guard_control','default_control','cancel_control','deinit_control','callback_control','isolation_control','invalidation_control'},
    'ghidra': {'binary', 'addresses'}, 'ghidra_mcp': {'tool', 'arguments'},
    'lldb_smoke': set(), 'frida_smoke': set(), 'native_reference': {'repeat_control','solid_control'},
    'connected_probe': set(), 'plist_corpus': {'seed','cases','decode_control'}, 'swift_metadata': {'binary','maximum','state_control'},
    'xcode_preview': {'variants','trace','scheme_control'}, 'xpc_corpus': {'seed','cases'},
    'xpc_negative':set(), 'xpc_prefix':set(), 'agent_discriminants':set(), 'raw_coder':set(), 'surface_corpus':{'gpu_control'}, 'preview_hook_smoke':set(), 'surface_ipc':{'exit_order','gpu_control','gpu_consumer_control','gpu_stall_control'}, 'surface_failure':{'control'}, 'surface_reuse':set(), 'xcode_bridge_probe':{'managed'}}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('w') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def load(path, default=None):
    path = pathlib.Path(path)
    return json.loads(path.read_text()) if path.exists() else default


def validate_experiment(e):
    required = {'id','adapter','hypothesis','depends_on','resources','timeout_seconds','artifact_limit_mb','params','priority','checks'}
    if set(e) != required:
        raise ValueError('experiment fields mismatch: ' + str(set(e) ^ required))
    import re
    if not isinstance(e['id'], str) or not re.fullmatch('[a-z][a-z0-9-]{1,63}', e['id']):
        raise ValueError('invalid experiment ID')
    if e['adapter'] not in ADAPTERS:
        raise ValueError('unknown adapter')
    if not isinstance(e['hypothesis'], str) or not e['hypothesis'].strip():
        raise ValueError('hypothesis required')
    for field in ['depends_on', 'resources']:
        if not isinstance(e[field], list) or not all(isinstance(v, str) and v for v in e[field]):
            raise ValueError('invalid ' + field)
    for field, maximum in [('timeout_seconds', 1800), ('artifact_limit_mb', 1024), ('priority', 100)]:
        if type(e[field]) is not int or not 1 <= e[field] <= maximum:
            raise ValueError('invalid ' + field)
    if not isinstance(e['params'], dict) or set(e['params']) - PARAMS[e['adapter']]:
        raise ValueError('unsupported adapter parameters')
    p = e['params']
    if 'payload' in p and p['payload'] not in ('IOSurfacePayload','RenderPayload','BitmapDescription','ServiceMessage','ServiceMessagePayload'):raise ValueError('Unsupported payload control')
    if 'guard_control' in p and type(p['guard_control']) is not bool:raise ValueError('Invalid guard control')
    if 'default_control' in p and type(p['default_control']) is not bool:raise ValueError('Invalid default control')
    if 'cancel_control' in p and type(p['cancel_control']) is not bool:raise ValueError('Invalid cancellation control')
    for flag in ('deinit_control','state_control','callback_control','isolation_control','invalidation_control','gpu_control','gpu_consumer_control','gpu_stall_control'):
        if flag in p and type(p[flag]) is not bool:raise ValueError('Invalid static state control')
    if 'decode_control' in p and type(p['decode_control']) is not bool:raise ValueError('Invalid decode control')
    if 'second_runtime' in p and type(p['second_runtime']) is not bool:raise ValueError('Invalid second runtime control')
    if 'repeat_control' in p and type(p['repeat_control']) is not bool:raise ValueError('invalid reference repeat control')
    if 'control' in p and p['control'] not in ('faults','use_state','late_ack'):raise ValueError('invalid surface control')
    if p.get('gpu_stall_control') is True and p.get('gpu_consumer_control') is not True:raise ValueError('GPU stall requires reviewed GPU consumer')
    if p.get('gpu_consumer_control') is True and p.get('gpu_control') is not True:raise ValueError('GPU consumer requires reviewed producer control')
    if e['adapter']=='surface_ipc' and p.get('gpu_control') is True and p.get('exit_order')!='receiver':raise ValueError('GPU handoff requires receiver-first mode')
    if 'exit_order' in p and p['exit_order'] not in ('sender','receiver'):raise ValueError('invalid exit_order')
    for field in ['xcode','binary','query','tool']:
        if field in p and (not isinstance(p[field], str) or not p[field] or len(p[field]) > 4096):
            raise ValueError('invalid parameter ' + field)
    if 'addresses' in p and (not isinstance(p['addresses'], list) or not p['addresses'] or
            len(p['addresses']) > 32 or not all(isinstance(v,str) and re.fullmatch('[0-9a-fA-F]{1,16}',v) for v in p['addresses'])):
        raise ValueError('invalid addresses')
    for field,maximum in [('seed',2**31-1),('cases',64),('maximum',5000)]:
        if field in p and (type(p[field]) is not int or not 1<=p[field]<=maximum):raise ValueError('Invalid '+field)
    if 'variants' in p and (not isinstance(p['variants'],list) or not 1<=len(p['variants'])<=4 or not all(type(v) is int and 0<=v<=16 for v in p['variants'])):raise ValueError('Invalid preview variants')
    if 'trace' in p and type(p['trace']) is not bool:raise ValueError('Invalid trace flag')
    if 'scheme_control' in p and type(p['scheme_control']) is not bool:raise ValueError('Invalid scheme control flag')
    if p.get('scheme_control') and (e['adapter']!='xcode_preview' or p.get('variants')!=[15,15,15]):raise ValueError('Scheme control requires owned definition 15 repeated three times')
    if 'arguments' in p and not isinstance(p['arguments'], dict):
        raise ValueError('arguments must be an object')
    if not isinstance(e['checks'], list) or not e['checks']:
        raise ValueError('at least one check required')
    for check in e['checks']:
        if not isinstance(check,dict) or set(check) != {'path','equals'} or not isinstance(check['path'],str) or not check['path']:
            raise ValueError('invalid check')
    return e


def validate_queue(queue):
    if not isinstance(queue,dict) or set(queue) != {'version','experiments'} or queue['version'] != 1 or not isinstance(queue['experiments'],list):
        raise ValueError('invalid queue')
    items = [validate_experiment(e) for e in queue['experiments']]
    ids = [e['id'] for e in items]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate experiment ID')
    for e in items:
        if set(e['depends_on']) - set(ids):
            raise ValueError('unknown dependency')
    visiting, done = set(), set()
    by_id = {e['id']:e for e in items}
    def visit(key):
        if key in visiting: raise ValueError('dependency cycle')
        if key in done: return
        visiting.add(key)
        for dep in by_id[key]['depends_on']: visit(dep)
        visiting.remove(key); done.add(key)
    for key in ids: visit(key)
    return queue


def evaluate(checks, result):
    observations = result.get('observations', {}) if isinstance(result,dict) else {}
    findings = []
    for check in checks:
        value = observations
        found = True
        for key in check['path'].split('.'):
            if not isinstance(value,dict) or key not in value:
                found = False; value = None; break
            value = value[key]
        passed = found and type(value) is type(check['equals']) and value == check['equals']
        findings.append({'path':check['path'], 'expected':check['equals'], 'actual':value, 'present':found, 'passed':passed})
    # Missing capture is inconclusive, not proof of absence.
    verdict = 'supports' if all(c['passed'] for c in findings) else 'inconclusive'
    return verdict, findings


def tree_size(path):
    total=0
    for p in pathlib.Path(path).rglob('*'):
        try:
            if p.is_file() and not p.is_symlink():total+=p.stat().st_size
        except FileNotFoundError:pass  # Compiler caches atomically replace temporary files.
    return total


def terminate_group(process):
    for sig, grace in [(signal.SIGTERM, 1), (signal.SIGKILL, 1)]:
        try: os.killpg(process.pid, sig)
        except ProcessLookupError: break
        if process.poll() is None:
            try: process.wait(timeout=grace)
            except subprocess.TimeoutExpired: pass
    if process.poll() is None: process.wait(timeout=2)


def execute(argv, directory, timeout, limit_bytes, event=None):
    started = time.monotonic()
    outcome = 'failed'
    process = None
    with (directory/'stdout.txt').open('wb') as stdout, (directory/'stderr.txt').open('wb') as stderr:
        try:
            env = dict(os.environ)
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            env['RE_PROJECT_ROOT'] = str(PROJECT_ROOT)
            env['PYTHONUNBUFFERED'] = '1'
            process = subprocess.Popen(argv, cwd=str(ROOT), stdout=stdout, stderr=stderr, env=env, start_new_session=True)
            if event: event('process_started', {'pid':process.pid, 'process_group':process.pid})
            next_update = started + 30
            while process.poll() is None:
                elapsed = time.monotonic() - started
                if elapsed >= timeout:
                    outcome = 'timed_out'; break
                if tree_size(directory) > limit_bytes:
                    outcome = 'artifact_limit'; break
                if time.monotonic() >= next_update:
                    if event: event('heartbeat', {'elapsed_seconds':round(elapsed,1)})
                    next_update += 30
                time.sleep(0.1)
            else:
                outcome = 'success' if process.returncode == 0 else 'failed'
        except (KeyboardInterrupt, SystemExit):
            outcome = 'interrupted'
        except OSError as error:
            stderr.write(str(error).encode())
        finally:
            if process is not None: terminate_group(process)
    if tree_size(directory) > limit_bytes: outcome = 'artifact_limit'
    return {'execution':outcome, 'exit_code':process.returncode if process else None,
            'duration_seconds':round(time.monotonic()-started,3)}


def source_files():
    excluded={'__pycache__','.build','.swiftpm'}
    suffixes={'.py','.m','.swift','.java','.sh','.js','.c','.entitlements','.pbxproj','.xcscheme'}
    return [p for p in sorted((ROOT/'tools/re').rglob('*')) if p.is_file() and not p.is_symlink() and p.suffix in suffixes and not excluded.intersection(p.parts)]


def identity():
    import importlib.metadata
    details = {'python':os.sys.version, 'packages':{}}
    for package in ['frida','frida-tools','Pillow']:
        try:details['packages'][package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:details['packages'][package]=None
    config_path=PROJECT_ROOT/'research/local-config.json'
    details['local_config_sha256']=digest(config_path) if config_path.is_file() else None
    from reloop.worker import ghidra_config
    home,java,_=ghidra_config()
    properties=pathlib.Path(home)/'Ghidra/application.properties' if home else None
    details['ghidra_properties_sha256']=digest(properties) if properties and properties.is_file() else None
    details['java_home']=java
    for name, argv in [('xcode',['xcodebuild','-version']), ('os',['sw_vers']), ('arch',['uname','-m'])]:
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=15)
            details[name] = {'exit_code':r.returncode,'value':r.stdout.strip()}
        except (OSError,subprocess.TimeoutExpired) as error:
            details[name] = {'error':type(error).__name__}
    image = pathlib.Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost')
    details['messaging_image_sha256'] = digest(image) if image.is_file() else None
    details['tool_sources'] = {str(p.relative_to(ROOT)):digest(p) for p in source_files()}
    return details


class Controller:
    def __init__(self, root=ROOT, state_root=None):
        self.root = pathlib.Path(root).resolve()
        self.state = pathlib.Path(state_root).resolve() if state_root else self.root/'research/state'
        self.runs = self.state.parent/'runs'
        self.state.mkdir(parents=True,exist_ok=True)
        self.runs.mkdir(parents=True,exist_ok=True)

    @contextlib.contextmanager
    def lock(self):
        with (self.state/'controller.lock').open('a+') as stream:
            try: fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: raise RuntimeError('another controller owns the experiment resources')
            try: yield
            finally: fcntl.flock(stream,fcntl.LOCK_UN)

    def journal(self, run, kind, payload):
        record = {'timestamp':now(), 'event':kind, **payload}
        with (run/'events.jsonl').open('a') as stream:
            stream.write(json.dumps(record,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
        if kind == 'heartbeat': print(json.dumps({'run':run.name, **record}),flush=True)

    def recover(self):
        # Holds the exclusive lock. Do not kill unknown/reused PIDs during recovery.
        for run in self.runs.iterdir():
            manifest = load(run/'manifest.json')
            if manifest and not manifest.get('sealed'):
                journal = (run/'events.jsonl').read_text() if (run/'events.jsonl').exists() else ''
                for line in journal.splitlines():
                    event = json.loads(line)
                    if event.get('event') == 'process_started':
                        try: os.kill(event['pid'], 0)
                        except ProcessLookupError: pass
                        except PermissionError: raise RuntimeError('Cannot verify interrupted process ownership; reconcile run '+run.name)
                        else: raise RuntimeError('Recorded interrupted process PID is still live; verify ownership before resuming '+run.name)
                manifest.update(execution='interrupted',verdict='not_evaluated',sealed=True,
                                finished_at=now(),recovery_note='Controller interrupted; surviving child ownership must be checked before native tracing.')
                self.journal(run,'recovered_interruption',{})
                manifest['artifacts'] = self.artifacts(run)
                atomic(run/'manifest.json',manifest)

    def artifacts(self,run):
        return [{'path':str(p.relative_to(run)), 'sha256':digest(p), 'bytes':p.stat().st_size}
                for p in sorted(run.rglob('*')) if p.is_file() and not p.is_symlink() and p != run/'manifest.json']

    def verify(self,run_id,expected_manifest_sha256=None):
        if not isinstance(run_id,str) or run_id in {'.','..'} or pathlib.Path(run_id).name != run_id: raise ValueError('invalid run ID')
        run = self.runs/run_id
        m = load(run/'manifest.json')
        if not m or not m.get('sealed'): raise ValueError('run missing or not sealed')
        actual = self.artifacts(run)
        artifact_hashes={a['path']:a['sha256'] for a in actual}
        frozen_unchanged=all(artifact_hashes.get('source/'+path)==sha
                             for path,sha in m.get('tool_source_hashes',{}).items())
        manifest_hash=digest(run/'manifest.json')
        if expected_manifest_sha256 is not None and not re.fullmatch('[0-9a-f]{64}',expected_manifest_sha256):
            raise ValueError('Invalid external manifest SHA-256')
        anchored=None if expected_manifest_sha256 is None else manifest_hash==expected_manifest_sha256
        return {'run_id':run_id,'valid':actual==m['artifacts'] and frozen_unchanged and anchored is not False,
                'manifest_sha256':manifest_hash,'external_anchor_matches':anchored,
                'frozen_sources_unchanged':frozen_unchanged,
                'scope':'Artifact consistency; authenticity requires a separately trusted manifest hash.'}

    def status(self):
        return load(self.state/'checkpoint.json',{'runs':{},'pending':[]})

    def ready(self,queue,checkpoint,environment):
        completed = set()
        for e in queue['experiments']:
            prior = checkpoint.get('runs',{}).get(e['id'])
            if not prior: continue
            m = load(self.runs/prior/'manifest.json',{})
            if (m.get('verdict')=='supports' and m.get('experiment_hash')==canonical_hash(e)
                    and m.get('environment_hash')==canonical_hash(environment) and self.verify(prior)['valid']):
                completed.add(e['id'])
        return sorted([e for e in queue['experiments'] if e['id'] not in completed and set(e['depends_on'])<=completed],key=lambda e:(-e['priority'],e['id']))

    def run_one(self,e,environment,seconds_left=None,bytes_left=None):
        validate_experiment(e)
        run_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+e['id']+'-'+uuid.uuid4().hex[:8]
        run = self.runs/run_id; run.mkdir()
        atomic(run/'experiment.json',e)
        try:
            commit = subprocess.run(['git','rev-parse','HEAD'],cwd=self.root,capture_output=True,text=True,timeout=5).stdout.strip()
            diff = subprocess.run(['git','diff','HEAD'],cwd=self.root,capture_output=True,timeout=5).stdout
        except (OSError,subprocess.TimeoutExpired): commit='unknown';diff=b''
        import shutil
        source = run/'source'
        for path in source_files():
            target=source/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        argv = [os.sys.executable,str(source/'tools/re/reloop/worker.py'),e['adapter'],'--out',str(run/'output'),'--params',json.dumps(e['params'])]
        code_hashes = {str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file()}
        if 'tool_sources' in environment:
            # The frozen executable inputs, rather than an earlier live scan, are authoritative.
            environment={**environment,'tool_sources':code_hashes}
        manifest = {'run_id':run_id,'started_at':now(),'experiment_id':e['id'],'hypothesis':e['hypothesis'],
                    'experiment_hash':canonical_hash(e),'environment':environment,'environment_hash':canonical_hash(environment),
                    'controller_loaded_source_sha256':LOADED_CONTROLLER_HASH,'git_commit':commit,'dirty_diff_hash':hashlib.sha256(diff).hexdigest(),'tool_source_hashes':code_hashes,
                    'argv':argv,'cwd':str(ROOT),'resources':e['resources'],'sealed':False}
        atomic(run/'manifest.json',manifest)
        self.journal(run,'experiment_started',{'experiment_id':e['id']})
        timeout=min(e['timeout_seconds'],seconds_left) if seconds_left is not None else e['timeout_seconds']
        limit=e['artifact_limit_mb']*1024*1024
        if bytes_left is not None: limit=min(limit,bytes_left)
        outcome=execute(argv,run,timeout,limit,lambda kind,payload:self.journal(run,kind,payload))
        try: result=load(run/'output/result.json',{})
        except (ValueError,OSError) as error: result={'observations':{},'invalid_result':str(error)}
        verdict,checks=evaluate(e['checks'],result) if outcome['execution']=='success' else ('not_evaluated',[])
        manifest.update(outcome,verdict=verdict,checks=checks,finished_at=now(),sealed=True)
        self.journal(run,'experiment_finished',{'execution':outcome['execution'],'verdict':verdict})
        manifest['artifacts']=self.artifacts(run)
        atomic(run/'manifest.json',manifest)
        return manifest

    def session(self,queue,max_experiments=8,minutes=45,max_mb=1024,only=None):
        validate_queue(queue)
        if not 1<=max_experiments<=100 or not 0<minutes<=1440 or not 1<=max_mb<=10240: raise ValueError('invalid session budget')
        with self.lock():
            self.recover()
            checkpoint=self.status();checkpoint.setdefault('runs',{})
            start=time.monotonic();used=0;attempted=set();results=[]
            if only and only not in {e['id'] for e in queue['experiments']}: raise ValueError('unknown experiment ID')
            for _ in range(max_experiments):
                environment=identity()
                remaining=minutes*60-(time.monotonic()-start)
                if remaining<=0 or used>=max_mb*1024*1024: break
                ready=[e for e in self.ready(queue,checkpoint,environment) if e['id'] not in attempted and (not only or e['id']==only)]
                if not ready: break
                e=ready[0];attempted.add(e['id'])
                print(json.dumps({'selected':e['id'],'hypothesis':e['hypothesis']}),flush=True)
                m=self.run_one(e,environment,remaining,max_mb*1024*1024-used)
                used+=tree_size(self.runs/m['run_id']);results.append(m)
                checkpoint['runs'][e['id']]=m['run_id'];checkpoint['updated_at']=now()
                checkpoint['environment_hash']=canonical_hash(environment)
                checkpoint['pending']=[e['id'] for e in self.ready(queue,checkpoint,environment)]
                atomic(self.state/'checkpoint.json',checkpoint)
                print(json.dumps({'run':m['run_id'],'execution':m['execution'],'verdict':m['verdict']}),flush=True)
                if m['execution'] in {'interrupted','artifact_limit','timed_out'}: break
            return [{'run_id':m['run_id'],'execution':m['execution'],'verdict':m['verdict']} for m in results]


LOADED_CONTROLLER_HASH = digest(__file__)
