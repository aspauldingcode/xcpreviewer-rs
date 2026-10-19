"""Read-only verification of a rejected numerical prediction and valid acquisition."""
from pathlib import Path
import json,hashlib,subprocess,sys
from phase_prerequisites import parsed,require as need
p=Path(__file__).resolve().parent;s=parsed((p/'seal.json').read_text());files={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and q.name!='seal.json' and '__pycache__' not in q.parts};need(files==set(s['files']),'inventory')
for n,h in s['files'].items():need(not (p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'seal')
for file in ['test-admission.py','test-recorded.py','admit.py','diagnose.py','exploratory-quantization.py']:
 for opt,label in [([], 'normal'),(['-O'],'optimized')]:
  z=subprocess.run([sys.executable,*opt,'-B',str(p/file)],capture_output=True,text=True,timeout=15);saved=parsed((p/(file+'.'+label+'.json')).read_text());need(z.returncode==saved['exit'],'exit')
  if file=='admit.py':need(z.returncode!=0 and 'primary/range contract' in z.stderr and 'primary/range contract' in saved['stderr'],'retained numerical rejection')
  elif file.startswith('test-'):need(z.returncode==0 and 'OK' in z.stderr and saved['exit']==0,'fault tests')
  else:need(z.returncode==0 and parsed(z.stdout)==parsed(saved['stdout']),'diagnostic replay')
r=parsed(parsed((p/'diagnose.py.normal.json').read_text())['stdout']);need(r['numerical_contract_rejected'] is True and r['all_bytes_compared']==175680 and r['primary_alpha_invariant_exact'] is False and r['opaque_gray_bit_exact_model_qualified'] is False and r['opaque_gray_conversion_operational_range'] is True,'scope')
need(r['comparisons'][0]['comparisons'][0]['mismatch_bytes']==9540 and r['comparisons'][1]['comparisons'][0]['mismatch_bytes']==0 and r['comparisons'][2]['comparisons'][1]['mismatch_bytes']==13824,'falsification')
print(json.dumps({'native_acquisition_verified':True,'numerical_contract_rejected':True,'all_bytes_compared':175680,'nonlinear_primary_mismatch_bytes':9540,'linear_primary_mismatch_bytes':0,'gray_IEC_mismatch_bytes':13824,'canvas_qualified':False}))
