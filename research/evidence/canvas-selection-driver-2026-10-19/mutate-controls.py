from pathlib import Path
import tempfile,subprocess,shutil,json,sys
p=Path(__file__).resolve().parent
mutants=[('abort-not-latched','selection-only.mjs','driver.abort(reason);','', 'test-selection-only.mjs'),('refresh-substitution','selection-only.mjs',"driver.action(result.assessment,'selection')","driver.action(result.assessment,'refresh')",'test-selection-only.mjs'),('effect-overclaim','selection-only.mjs','effect_verified:false','effect_verified:true','test-selection-only.mjs'),('action-clock-wrong-unit','selection-registry.mjs','clock().wall*1000','clock().wall','test-selection-registry.mjs'),('workspace-not-bound','selection-registry.mjs',"for(const key of ['projects','sources'])if", "for(const key of [])if",'test-selection-registry.mjs')]
if True:
 results=[]
 for name,file,old,new,test in mutants:
  with tempfile.TemporaryDirectory(prefix='selection-mutant-',dir='/private/tmp') as tmp:
   d=Path(tmp)
   for n in p.glob('*.mjs'):shutil.copy2(n,d/n.name)
   for n in ['binding.json','prior-final-projection.ax.txt']:shutil.copy2(p/n,d/n)
   f=d/file;s=f.read_text()
   if s.count(old)!=1:raise ValueError('mutation anchor '+name)
   f.write_text(s.replace(old,new))
   subprocess.run(['node','--check',str(f)],check=True,capture_output=True,timeout=10)
   x=subprocess.run(['node',str(d/test)],capture_output=True,text=True,timeout=10)
   if x.returncode==0:raise ValueError('undetected '+name)
   # Evidence paths remain synthetic temp paths; no app binary or private dump.
   results.append({'mutant':name,'syntax_valid':True,'rejected':True,'returncode':x.returncode,'stdout':x.stdout,'stderr':x.stderr.replace(tmp,'<owned-mutant-directory>')})
 if '--verify' not in sys.argv:(p/'mutations.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps({'syntactically_valid_mutants_rejected':len(results)}))
