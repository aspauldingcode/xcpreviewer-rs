"""Frozen Python-only replay; never imports a Node provider or starts a process probe."""
from pathlib import Path
import json,subprocess,sys
from phase_prerequisites import parsed,require as need
import admit as a
p=Path(__file__).resolve().parent;seal=parsed((p/'seal.json').read_text())
files={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and q.name!='seal.json' and '__pycache__' not in q.parts};need(files==set(seal['files']),'inventory')
for n,h in seal['files'].items():
 q=p/n;need(not q.is_symlink() and q.resolve().is_relative_to(p) and a.H(q.read_bytes())==h,'sealed member')
quarantine=parsed((p/'retained-source-capture-collision.json').read_text());need(quarantine['quarantined_from_source_claims'] is True and quarantine['executed_ExecFileOutput_source_affected'] is False,'capture quarantine')
for claim in parsed((p/'source-locators.json').read_text())['claims']:
 q=p/claim['source'];raw=q.read_text();start,end=claim['char_span'];need(claim['source']!=quarantine['original_member'] and a.H(raw.encode())==claim['source_sha256'] and raw[start:end]==claim['quote'] and claim['line_span']==[raw[:start].count('\n')+1,raw[:end].count('\n')+1] and claim['UI_runtime_observed'] is False,'static locator')
for name,count in [('test_admission.py',4),('test_recorded.py',4),('admit.py',0)]:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/name)],capture_output=True,text=True,timeout=15);saved=parsed((p/(name+'.'+label+'.json')).read_text());need(z.returncode==saved['exit']==0,'verification exit')
  if count:need(('Ran %d tests'%count) in z.stderr and 'OK' in z.stderr and 'OK' in saved['stderr'],'fault controls')
  else:need(parsed(z.stdout)==parsed(saved['stdout']),'saved result')
v=a.observed(p);need(v['marker_bytes_compared']==2048 and v['default_abort_settles_before_owned_exit_and_late_write'] is True and v['stoppable_abort_settles_after_owned_close'] is True and v['provider_target_UI_settlement_qualified'] is False,'scope')
print(json.dumps(v,sort_keys=True))
