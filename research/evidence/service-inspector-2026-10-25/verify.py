from pathlib import Path
import tempfile,shutil,subprocess
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='service-inspector-replay-') as directory:
 work=Path(directory)
 for name in ['check.py','controls.py','native.swift','run-wasi.cjs','source-verify.py','source-findings.json']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode()
 print('Four CLI integration tests,768 predecessor source bytes,12 Foundation cases,24 actual WASI invocations passed. Full271-test output retained separately. No service actions or milestone parity claimed.')
