import hashlib,importlib.util,json,shutil,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/8amps/xcpreviewer-rs')
CASES={'verify_completion_guard.py':('completion-guard-corrected-2026-10-14','delayed-zero'),'verify_post_completion_delay.py':('post-completion-delay-2026-10-14','delayed')}
def reseal(e):
 files={str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 (e/'manifest.json').write_text(json.dumps({'files':files}))
def mutate(e,mode,fault):
 p=e/mode/'result.json';v=json.loads(p.read_text())
 if fault=='wait':v['record']['report']['target_code']=71
 elif fault=='drain':v['record']['report']['drained']=False
 elif fault=='hash':v['record']['stdoutSha256']='0'*64
 elif fault=='payload':(e/mode/'owned.raw').write_bytes(b'bad-data')
 elif fault=='terminal-time':
  p2=e/mode/'deadline-audit.jsonl';rows=[json.loads(s) for s in p2.read_text().splitlines()];next(x for x in rows if x['kind']=='target_poll' and x['code'] is not None)['value']=100.0;p2.write_text(''.join(json.dumps(x)+'\n' for x in rows))
 p.write_text(json.dumps(v));reseal(e)
def check(source,e,optimized):
 code='import importlib.util,sys;s=importlib.util.spec_from_file_location("consumer",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.verify(sys.argv[2])'
 x=subprocess.run([sys.executable,*(['-O'] if optimized else []),'-B','-c',code,str(source),str(e)],capture_output=True,timeout=10)
 return {'accepted':x.returncode==0,'code':x.returncode,'stderr':x.stderr.decode()[-350:]}
def main():
 results=[]
 for name,(folder,mode) in CASES.items():
  anchor=ROOT/'research/evidence'/folder
  for fault in ['positive','wait','drain','hash','payload','terminal-time']:
   with tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(anchor,e)
    if fault!='positive':mutate(e,mode,fault)
    for version in ['original','fixed']:
     source=HERE/(('original-' if version=='original' else '')+name)
     for optimized in [False,True]:
      v=check(source,e,optimized);v.update(consumer=name,fault=fault,version=version,optimized=optimized);results.append(v)
      expected=fault=='positive' or (version=='original' and optimized)
      if v['accepted']!=expected:raise ValueError(v)
 (HERE/'matrix.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'configurations':len(results),'optimized_original_false_acceptances':sum(v['accepted'] and v['fault']!='positive' and v['version']=='original' for v in results),'frozen_native_runs_added':0}))
if __name__=='__main__':main()
