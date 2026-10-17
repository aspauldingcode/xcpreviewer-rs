import hashlib,json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
s=json.loads((p/'seal.json').read_text())
for n,h in s['files'].items():
 f=p/n
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=h:raise ValueError('Seal mismatch: '+n)
parent=json.loads((p/'parent-seal.json').read_text())
if hashlib.sha256((p/'parent-seal.json').read_bytes()).hexdigest()!='acd4b8b7f5ca0bab97dfef7a13cc0f438f5dbaac2c5e56469c7a7ca67b45896c':raise ValueError('Parent anchor changed')
for n in ['phase_prerequisites.py','execute.py','pre-fix-execute.py']:
 if hashlib.sha256((p/'candidate'/n).read_bytes()).hexdigest()!=parent['files'][n]:raise ValueError('Candidate drift')
if hashlib.sha256((p/'pre-audit-tests.py').read_bytes()).hexdigest()!=parent['files']['test_phase_prerequisites.py']:raise ValueError('Original tests drift')
sys.path.insert(0,str(p));from audit import audit
for test,filename,expected in [('pre-audit-tests.py','initial-results.json',{'skip-control-args','skip-owned-pid-range','skip-finite-walk'}),('test_phase_prerequisites.py','corrected-results.json',set())]:
 actual=audit(test);frozen=json.loads((p/filename).read_text())
 def semantic(rows):return [(r['mutant'],r['optimized'],r['returncode'],r['source_sha256']) for r in rows]
 if semantic(actual)!=semantic(frozen):raise ValueError('Mutation outcome changed')
 if {r['mutant'] for r in actual if r['mutant']!='baseline' and r['returncode']==0}!=expected:raise ValueError('Unexpected survivor set')
 if any(r['returncode']!=0 for r in actual if r['mutant']=='baseline'):raise ValueError('Baseline failure')
print(json.dumps({'files_verified':len(s['files']),'test_suite_subprocesses':24,'original_surviving_mutants':3,'corrected_surviving_mutants':0,'native_jobs':0,'independent_review':'pending'}))
