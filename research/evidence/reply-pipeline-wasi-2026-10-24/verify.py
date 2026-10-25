from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='reply-wasi-replay-') as directory:
    work=Path(directory)
    for name in ['check.py','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
    result=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=180)
    if result.returncode:print((result.stdout+result.stderr).decode())
    result.check_returncode()
    for name in ['native.stdout','wasi.stdout']:assert (work/name).read_bytes()==(artifact/name).read_bytes()
    print('Actual native and WASI reply-pipeline execution replayed with identical output; no native settlement claim.')
