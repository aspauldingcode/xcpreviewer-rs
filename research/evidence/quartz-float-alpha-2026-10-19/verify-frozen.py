"""Frozen Python-only verification; never compiles or executes native code."""
from pathlib import Path
import json
import subprocess
import sys
import compare as c
p=Path(__file__).resolve().parent
seal=c.parsed((p/'seal.json').read_text())
files={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and q.name!='seal.json' and '__pycache__' not in q.parts}
c.require(files==set(seal['files']),'inventory')
for n,sha in seal['files'].items():
 q=p/n;c.require(not q.is_symlink() and q.resolve().is_relative_to(p) and c.digest(q.read_bytes())==sha,'sealed member')
for name,count in [('test_compare.py',6),('test_acquire.py',10),('test_recorded.py',3),('acquire.py',0),('diagnose.py',0),('strict-identity.py',0)]:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/name)],capture_output=True,text=True,timeout=15)
  saved=c.parsed((p/(name+'.'+label+'.json')).read_text())
  c.require(z.returncode==saved['exit'],'saved exit')
  if name=='strict-identity.py':c.require(z.returncode!=0 and 'independent identity prediction rejected' in z.stderr and 'independent identity prediction rejected' in saved['stderr'],'retained numerical rejection')
  elif count:c.require(z.returncode==0 and ('Ran %d tests'%count) in z.stderr and 'OK' in z.stderr and 'OK' in saved['stderr'],'fault controls')
  else:c.require(z.returncode==0 and c.parsed(z.stdout)==c.parsed(saved['stdout']),'comparison replay')
v=c.parsed(c.parsed((p/'acquire.py.normal.json').read_text())['stdout'])
c.require(v['all_bytes_compared']==172416 and v['native_acquisition_qualified'] is True and v['linear_identity_control'] is True and v['canvas_qualified'] is False,'scoped result')
c.require(v['routes'][0]['identity']['mismatch_bytes']==702 and v['routes'][0]['historical_8bit_relation']['mismatch_bytes']==9540 and v['routes'][1]['identity']['exact'] is True,'retained models')
d=c.parsed(c.parsed((p/'diagnose.py.normal.json').read_text())['stdout'])
c.require(d['post_acquisition_field_localization']['identity']=={'alpha':0,'designated_primary':702,'other_rgb':0} and d['measured_samples_used_as_goldens'] is False,'field diagnosis')
print(json.dumps({'native_acquisition_verified':True,'linear_identity_control':True,'all_bytes_compared':172416,'nonlinear_identity_mismatch_bytes':702,'historical_8bit_mismatch_bytes':9540,'strict_identity_rejected':True,'canvas_qualified':False}))
