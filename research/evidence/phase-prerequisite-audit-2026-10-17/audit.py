"""Finite mutation audit: Python tests with fake dispatch only, never native jobs."""
import ast,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE/'candidate'
MUTANTS={
 'skip-control-args':("        require(row['args'] == ['--output-control', 'output-valid'], 'Wrong control args')\n",''),
 'skip-owned-pid-range':("        require(1 < pid <= 2147483647, 'Invalid owned PID')\n",''),
 'skip-finite-walk':('    finite(value)\n',''),
 'skip-control-dependency':("            receipt(root, 'output-valid', source_hash, binary_hash)\n",'            pass\n'),
 'skip-stderr-integrity':("    require(len(err) <= 131072 and integer(record['stderrBytes'], len(err))\n            and record['stderrSha256'] == hashlib.sha256(err).hexdigest(),\n            'Captured diagnostics changed')\n",''),
}

def audit(test_name):
 source=(BASE/'phase_prerequisites.py').read_text();results=[]
 for name,edit in [('baseline',None),*MUTANTS.items()]:
  candidate=source
  if edit:
   old,new=edit
   if source.count(old)!=1:raise ValueError('Mutation not exact: '+name)
   candidate=source.replace(old,new)
  ast.parse(candidate)
  for optimized in [False,True]:
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    for n in ['execute.py','pre-fix-execute.py']:shutil.copyfile(BASE/n,root/n)
    shutil.copyfile(HERE/test_name,root/'test_phase_prerequisites.py')
    (root/'phase_prerequisites.py').write_text(candidate)
    x=subprocess.run([sys.executable,*(['-O'] if optimized else []),'-B',str(root/'test_phase_prerequisites.py')],capture_output=True,text=True,timeout=15)
    if 'Ran ' not in x.stderr or 'SyntaxError' in x.stderr or 'ImportError' in x.stderr:raise ValueError('Invalid mutation execution: '+name+x.stderr)
    results.append({'mutant':name,'optimized':optimized,'returncode':x.returncode,'source_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'stdout':x.stdout,'stderr':x.stderr})
 return results
if __name__=='__main__':
 test=sys.argv[1];out=Path(sys.argv[2]);result=audit(test);out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'test':test,'survivors':[r['mutant'] for r in result if r['mutant']!='baseline' and r['returncode']==0],'baseline_passes':all(r['returncode']==0 for r in result if r['mutant']=='baseline')}))
