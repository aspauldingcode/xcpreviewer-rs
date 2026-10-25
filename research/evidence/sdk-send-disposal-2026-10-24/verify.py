from pathlib import Path
import tempfile,shutil,subprocess,json
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='sdk-send-disposal-replay-') as directory:
 work=Path(directory)
 for name in ['OwnedSendTrace.h','OwnedSendTrace.c','probe.m','build.py','check.py','source-verify.py','caller-findings.json']:shutil.copyfile(artifact/name,work/name)
 p=subprocess.run(['python3',str(work/'check.py')],capture_output=True,timeout=100)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode()
 for mode in ['normal','cancel']:
  actual=json.loads((work/(mode+'-sanitized.json')).read_text());golden=json.loads((artifact/(mode+'-sanitized.json')).read_text())
  assert actual['marker_observations']==golden['marker_observations']
  assert actual['local_dead_name_retirement_observed']==golden['local_dead_name_retirement_observed']
 print('Owned positive Mach2 send and canceled libxpc destruction/local-name retirement replay passed;96 caller bytes independently verified. Prior250 Rust/WASI baseline unchanged, not rerun. Global/private target settlement and failed-kernel-send route remain open.')
