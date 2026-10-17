from pathlib import Path
s=Path('/private/tmp/surface-cross-move-20261017');d=Path('/private/tmp/surface-queue-owner-20261017');d.mkdir(exist_ok=False)
for n in ['surface_ipc_probe.c','run_guard.js','execute.py','run_before_deadline.py','observed_compiler.js','observed_group_anchor.py','sdk-identity.json','environment.json','test_gate.py','pre-lock-only-execute.py','record_admit.py','verify-frozen.py']:
 t=(s/n).read_text()
 if n in ['execute.py','run_before_deadline.py','test_gate.py']:t=t.replace('17,51,7','18,1,7').replace('2026-10-17T17:51:07','2026-10-17T18:01:07')
 (d/n).write_text(t)
t=(s/'probe.c').read_text();prefix=t[:t.index('static int receiver(')].replace('// Paired COPY/MOVE initial descriptor; CF-held recovery after receive-size error.','// Queue-held handoff after sender-owned CF and Mach resource references release.')
(d/'probe.c').write_text(prefix)
for kind in ['copy','move']:
 for mode in ['control','large','small']:(d/'owned-documents'/(kind+'-'+mode)).mkdir(parents=True)
