from pathlib import Path
import tempfile,subprocess,shutil,json,sys
p=Path(__file__).resolve().parent
mutants=[('old-wrapper-not-retired','previous.app.getAXState=retired;previous.app.click=retired;',''),('late-click-result-allowed','const value=await app.click(index,options);check();','const value=await app.click(index,options);'),('late-AX-result-allowed','const value=await app.getAXState(options);check();','const value=await app.getAXState(options);'),('boolean-zero-accepted','closure.owned_workspace_windows_after===0','closure.owned_workspace_windows_after!==1'),('closed-holder-allowed',"need(!closed,'holder closed');",'')]
results=[]
for name,old,new in mutants:
 with tempfile.TemporaryDirectory(prefix='handoff-mutant-',dir='/private/tmp') as tmp:
  d=Path(tmp)
  for n in p.glob('*.mjs'):shutil.copy2(n,d/n.name)
  for n in ['binding.json','prior-final-projection.ax.txt']:shutil.copy2(p/n,d/n)
  f=d/'handoff.mjs';s=f.read_text()
  if s.count(old)!=1:raise ValueError('mutation anchor '+name)
  f.write_text(s.replace(old,new));subprocess.run(['node','--check',str(f)],check=True,capture_output=True,timeout=10)
  x=subprocess.run(['node',str(d/'test-handoff.mjs')],capture_output=True,text=True,timeout=10)
  if x.returncode==0:raise ValueError('undetected '+name)
  results.append({'mutant':name,'syntax_valid':True,'rejected':True,'returncode':x.returncode,'stderr':x.stderr.replace(tmp,'<owned-mutant-directory>')})
if '--verify' not in sys.argv:(p/'mutations.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({'syntactically_valid_mutants_rejected':len(results),'native_execution':False}))
