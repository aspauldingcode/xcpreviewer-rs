import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from reloop import rustidentity


def run(evidence):
    config = json.loads((evidence/'config.json').read_text())
    original_run = rustidentity.subprocess.run
    original_file = rustidentity.file_identity
    for index in range(2):
        queries = []
        files = []
        def query(*args, **kwargs):
            started = time.monotonic()
            result = original_run(*args, **kwargs)
            queries.append({'command':args[0],'elapsed_seconds':time.monotonic()-started,'wait_code':result.returncode,'stdout_bytes':len(result.stdout),'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_bytes':len(result.stderr),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()})
            return result
        def file_identity(path):
            started = time.monotonic()
            result = original_file(path)
            files.append({'path':str(path),'elapsed_seconds':time.monotonic()-started,'identity':result})
            return result
        rustidentity.subprocess.run = query
        rustidentity.file_identity = file_identity
        started = time.monotonic()
        try:
            identity, digest = rustidentity.snapshot(config['rustc'])
            result = {'identity':identity,'digest':digest,'elapsed_seconds':time.monotonic()-started,'queries':queries,'files':files}
            (evidence/('snapshot-'+str(index)+'.json')).write_text(json.dumps(result,indent=2)+'\n')
            assert digest == config['toolchainPin']
            print(index,digest,result['elapsed_seconds'],flush=True)
        finally:
            rustidentity.subprocess.run = original_run
            rustidentity.file_identity = original_file


if __name__ == '__main__':
    run(Path(sys.argv[1]))
