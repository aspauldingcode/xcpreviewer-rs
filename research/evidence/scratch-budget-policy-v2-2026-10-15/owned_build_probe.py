"""One research-only owned build with separately bounded scratch measurements."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from scratch_budget import admit, new_root


def bounded_measure(root, identity):
    # The measurement child has no child processes; subprocess.run kills and
    # waits it on timeout. The outer monitor never trusts partial JSON.
    code = ('import json,sys,time;sys.path.insert(0,sys.argv[1]);'
            'from scratch_budget import measure;'
            'print(json.dumps(measure(sys.argv[2],identity=tuple(map(int,sys.argv[3:5])), '
            'deadline=time.monotonic()+1,max_entries=100000)))')
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    result = subprocess.run([sys.executable, '-S', '-c', code,
                             str(Path(__file__).parent), str(root), *map(str, identity)],
                            env=env, capture_output=True, text=True, check=True, timeout=2)
    return json.loads(result.stdout)


def probe(project, parent, observer, owned_tree):
    root, identity = new_root(parent)
    argv = ['/usr/bin/xcrun', 'xcodebuild', '-project', str(project),
            '-scheme', 'PreviewLab', '-configuration', 'Debug', '-sdk', 'macosx',
            '-destination', 'platform=macOS,arch=arm64', '-destination-timeout', '3',
            '-derivedDataPath', str(root / 'DerivedData'), 'CODE_SIGNING_ALLOWED=NO', 'build']
    report = {'scope': 'Owned build only; no native Canvas acceptance',
              'root': str(root), 'root_identity': identity, 'argv': argv,
              'outcome': 'not_started', 'samples': []}
    process = None
    tree = None
    started = time.monotonic()
    try:
        observer()
        with (root / 'stdout.txt').open('wb') as stdout, (root / 'stderr.txt').open('wb') as stderr:
            process = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
            tree = owned_tree(process.pid, process, snapshotter=observer)
            tree.observe()
            while process.poll() is None:
                tree.observe()
                values = bounded_measure(root, identity)
                report['samples'].append(values)
                if not admit(values):
                    report['outcome'] = 'artifact_limit'
                    break
                if time.monotonic() - started >= 40:
                    report['outcome'] = 'timed_out'
                    break
                time.sleep(0.1)
            else:
                report['outcome'] = 'success' if process.returncode == 0 else 'failed'
    except Exception as error:
        report['outcome'] = 'observation_failed'
        report['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        try:
            if tree is not None:
                report['cleanup'] = tree.drain()
        finally:
            if process is not None:
                # Fallback affects only this still-live owned root.
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=2)
                report['exit_code'] = process.returncode
            report['seconds'] = time.monotonic() - started
            try:
                report['final_measure'] = bounded_measure(root, identity)
                if not admit(report['final_measure']):
                    report['outcome'] = 'artifact_limit'
            except Exception as error:
                report['outcome'] = 'observation_failed'
                report['final_measure_error'] = str(error)
            (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report
