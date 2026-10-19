"""One owned offline container, fixed deadline and label-verified cleanup."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,sys,time
r=Path('/Users/8amps/xcpreviewer-rs');p=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.linuxwasm import verify_runtime
from container_control import cleanup as cleanup_owned,docker_command
from phase_prerequisites import parsed,require as need
H=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
with Controller().lock():
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(H(p/n)==h,'approved pin')
 plan=parsed((p/'plan.json').read_text());rea=parsed((p/'rea-identity.json').read_text());runtime=Path(plan['runtime_root'])
 need(rea['sha256']==plan['wheel_sha256'] and rea['closed'] is True and rea['format']=='zip','REA runtime carrier')
 need(H(r/'tools/re/reloop/linuxwasm.py')==plan['runtime_validator_sha256'],'runtime validator drift');verify_runtime(runtime)
 def call(args,timeout=8):return subprocess.run(['docker','--context',plan['context'],*args],capture_output=True,text=True,timeout=timeout)
 image=call(['image','inspect','--format','{"id":{{json .Id}},"os":{{json .Os}},"architecture":{{json .Architecture}}}',plan['image']]);image.check_returncode();need(parsed(image.stdout)==plan['image_identity'],'cached image changed')
 before=call(['ps','-a','--no-trunc','--format','{{.ID}} {{.Names}}']);before.check_returncode()
 need(all(line.split()[-1]!=plan['name'] for line in before.stdout.splitlines()),'owned name already exists')
 need(time.time()+90<datetime.datetime(2026,10,19,17,20,tzinfo=datetime.timezone.utc).timestamp(),'fixed deadline reserve')
 with (p/'started.json').open('x') as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deadline_utc':'2026-10-19T17:20:00Z'},f)
 stage=r/'research/build'/('linux-memory-growth-'+plan['owner']);stage.mkdir();output=stage/'owned-output';output.mkdir()
 for n in ['runner.py','probe.wasm']:shutil.copy2(p/n,stage/n)
 command=docker_command(plan)[3:]
 execution={'command':['docker','--context',plan['context'],*command],'deadline_utc':'2026-10-19T17:20:00Z','executions':1,'retry':False,'exit':None,'stdout':'','stderr':'','timeout':False}
 try:
  try:
   q=call(command,30);execution.update(exit=q.returncode,stdout=q.stdout,stderr=q.stderr,timeout=False)
  except subprocess.TimeoutExpired as e:
   plain=lambda v:v.decode() if isinstance(v,bytes) else v or '';execution.update(exit=None,stdout=plain(e.stdout),stderr=plain(e.stderr),timeout=True)
  execution['fixture_completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 finally:
  execution.setdefault('fixture_completed_at',datetime.datetime.now(datetime.timezone.utc).isoformat());(p/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
  def retain_cleanup(report):
   report['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(p/'container-cleanup.json').write_text(json.dumps(report,indent=2)+'\n')
  cleanup=cleanup_owned(call,plan,retain_cleanup)
  after=call(['ps','-a','--no-trunc','--format','{{.ID}} {{.Names}}']);after.check_returncode()
  inventory={'before':before.stdout.splitlines(),'after':after.stdout.splitlines(),'existing_preserved':set(before.stdout.splitlines())<=set(after.stdout.splitlines())}
  (p/'existing-containers.json').write_text(json.dumps(inventory,indent=2)+'\n')
  execution['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(p/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
  for f in output.iterdir():need(f.is_file() and not f.is_symlink(),'unexpected owned output');shutil.copy2(f,p/'owned-output'/f.name)
 need(cleanup['remaining_exit']==0 and cleanup['remaining']=='' and (cleanup['cleanup_exit'] is None or type(cleanup['cleanup_exit']) is int and cleanup['cleanup_exit']==0) and inventory['existing_preserved'] is True,'owned cleanup/preservation')
 verify_runtime(runtime)
 (p/'runtime-validation.json').write_text(json.dumps({'before':True,'after':True,'wheel_sha256':plan['wheel_sha256'],'validator_sha256':plan['runtime_validator_sha256']},indent=2)+'\n')
 need(execution['exit']==0 and execution['timeout'] is False,'container execution failed')
 print(json.dumps({'exit':execution['exit'],'owned_cleanup_verified':True,'existing_containers_preserved':True,'retry':False}))
