import datetime,hashlib,json,os,shutil,subprocess,sys,time,uuid
from pathlib import Path
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
from reloop.core import Controller
p=Path('/private/tmp/container-isolation-20261019'); repo=Path('/Users/8amps/xcpreviewer-rs')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
with Controller().lock():
 p.mkdir(exist_ok=False); owner=uuid.uuid4().hex; name='xcpreviewer-isolation-'+owner[:12]; image='sha256:4d93e034ce6cd5ed51447f399bc76b0d9b45fcb47dd0175ee928a3848ab35109'; stage=repo/'research/build'/('clean-isolation-'+owner)
 def call(args,timeout=8):return subprocess.run(['docker','--context','colima']+args,capture_output=True,text=True,timeout=timeout)
 inspect=call(['image','inspect','--format','{{json .Id}}',image]); inspect.check_returncode()
 if json.loads(inspect.stdout)!=image:raise RuntimeError('image changed')
 before=call(['ps','-a','--no-trunc','--format','{{.ID}} {{.Names}}']);before.check_returncode();(p/'containers-before.txt').write_text(before.stdout)
 stage.mkdir(); inp=stage/'input';out=stage/'output'; excluded=stage/'excluded'
 for d in [inp,out,excluded]:d.mkdir(mode=0o700)
 control=bytes(i%256 for i in range(1024));(inp/'CONTROL.bin').write_bytes(control);(excluded/'CONTROL.bin').write_bytes(b'EXCLUDED ORIGINAL CONTROL\n')
 (inp/'absolute-escape').symlink_to(excluded/'CONTROL.bin');(inp/'relative-escape').symlink_to('../excluded/CONTROL.bin')
 shutil.copyfile('/private/tmp/container-isolation-runner.py',stage/'runner.py')
 args=['run','--rm','--pull','never','--name',name,'--label','xcpreviewer.owner='+owner,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','--cpus','1','--user',str(os.getuid())+':'+str(os.getgid()),'--env','PYTHONDONTWRITEBYTECODE=1','--env','EXCLUDED_HOST_PATH='+str(excluded/'CONTROL.bin'),'--mount','type=bind,src='+str(inp)+',dst=/input,readonly','--mount','type=bind,src='+str(out)+',dst=/work','--mount','type=bind,src='+str(stage/'runner.py')+',dst=/runner.py,readonly','--entrypoint','/app/.venv/bin/python3',image,'-B','/runner.py']
 plan={'scope':'Container subprocess mount boundary only; no fresh model/tool isolation or approved spec handoff.','prediction':'Exact1024-byte input and reversed output pass; readonly input/root writes return EROFS; unmounted host/research/escape reads return ENOENT.','commands':1,'image':image,'owner':owner,'name':name,'args':['docker','--context','colima']+args,'fixed_deadline_utc':'2026-10-19T21:34:00Z','timeout_seconds':25,'runner_alarm_seconds':15,'stage':str(stage),'new_user_containers_preserved':before.stdout.splitlines(),'native_canvas_executed':False,'product_agent_launched':False}
 (p/'plan.json').write_text(json.dumps(plan,indent=2));shutil.copyfile(stage/'runner.py',p/'runner.py')
 if time.time()+60>=datetime.datetime(2026,10,19,21,34,tzinfo=datetime.timezone.utc).timestamp():raise RuntimeError('fixed deadline reserve')
 with (p/'started.json').open('x') as f:json.dump({'started_at':now()},f)
 try:
  try:
   r=call(args,25);execution={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'timeout':False,'finished_at':now()}
  except subprocess.TimeoutExpired as e:execution={'exit':None,'timeout':True,'finished_at':now(),'stderr':str(e)}
  (p/'execution.json').write_text(json.dumps(execution,indent=2))
 finally:
  probe=call(['inspect','--format','{{index .Config.Labels "xcpreviewer.owner"}}',name]);cleanup={'inspect_exit':probe.returncode,'inspect_owner':probe.stdout.strip(),'removed':False}
  if probe.returncode==0:
   if probe.stdout.strip()!=owner:raise RuntimeError('foreign container refusing cleanup')
   rm=call(['rm','-f',name]);cleanup['removed']=rm.returncode==0
  remaining=call(['ps','-a','--filter','name=^/'+name+'$','--format','{{.Names}}']);cleanup.update(remaining_exit=remaining.returncode,remaining=remaining.stdout.strip(),completed_at=now());(p/'cleanup.json').write_text(json.dumps(cleanup,indent=2))
  after=call(['ps','-a','--no-trunc','--format','{{.ID}} {{.Names}}']);after.check_returncode();(p/'containers-after.txt').write_text(after.stdout)
  if not set(before.stdout.splitlines())<=set(after.stdout.splitlines()):raise RuntimeError('preexisting inventory changed')
  if remaining.returncode or remaining.stdout.strip():raise RuntimeError('owned cleanup unverified')
  for f in out.iterdir():
   if f.is_file() and not f.is_symlink():shutil.copyfile(f,p/f.name)
 if execution['exit']!=0 or execution['timeout']:raise RuntimeError('control execution failed')
 if (inp/'CONTROL.bin').read_bytes()!=control or (p/'result.bin').read_bytes()!=bytes(255-(i%256) for i in range(1024)):raise RuntimeError('complete file bytes mismatch')
 print(json.dumps({'passed':True,'root':str(p),'owned_cleanup_verified':True,'preexisting_containers_preserved':True}))
