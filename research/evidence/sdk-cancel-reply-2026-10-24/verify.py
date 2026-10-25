from pathlib import Path
import tempfile,shutil,subprocess
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='sdk-cancel-reply-replay-') as directory:
 work=Path(directory)
 for name in ['OwnedXpcCancelReply.m','source-verify.py','findings.json','runtime-layout.json','observed.bplist','check.py','wasi.rs','run-wasi.cjs']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();assert (work/'wasi.stdout').read_bytes()==(artifact/'wasi.stdout').read_bytes()
 print('Current source/libxpc identity,250 Rust tests,two actual owned SDK cancellation/capture controls and WASI projection/capture checks passed. Private service callbacks/target settlement and global exactly-once remain unproven.')
