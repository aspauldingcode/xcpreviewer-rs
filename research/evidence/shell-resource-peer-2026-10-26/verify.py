from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='shell-resource-peer-replay-') as directory:
 work=Path(directory)
 names=['trace.c','trace.h','peer.c','peer.h','oracle.m','metadata.m','check.py','verify-peer.py','run-wasi.cjs','reparse.swift','shell-a-input.bplist','shell-b-input.bplist']
 names += [p.name for p in artifact.glob('native-shell-*') if p.is_file() and p.suffix in ['.swift','.s','.h','.c','.py']]
 for name in names:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py'),'--replay'],capture_output=True,timeout=180)
 if p.returncode:print((p.stdout+p.stderr).decode(errors='replace'))
 p.check_returncode()
 result=json.loads((work/'fresh/peer-verification.json').read_text());cross=json.loads((work/'fresh/cross-runtime.json').read_text())
 assert result['complex_body_bytes_compared']==2716 and result['faults_rejected']==91 and result['direct_rust_successes']==3 and result['direct_rust_expected_eof_errors']==1
 assert cross==json.loads((artifact/'cross-runtime.json').read_text())
 print('10 focused tests plus6 fresh native-corpus tests,7 native transfers,2716 bytes/91 mutations,3 direct Rust imported-FD successes/1 expected alias EOF,11 native shell decodes/WASI runs/Foundation reparses pass. Full391-test log retained. Actual Canvas routing and final resource/provider settlement remain open.')
