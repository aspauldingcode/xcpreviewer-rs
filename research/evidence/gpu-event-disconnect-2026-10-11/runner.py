import pathlib,os,sys,subprocess,json,hashlib,plistlib,uuid,re,time
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');os.chdir(r);sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 e=r/'research/evidence/gpu-event-disconnect-2026-10-11';target=pathlib.Path('/private/tmp/xcpreviewer-gpu-event-disconnect')
 c=subprocess.run(['xcrun','clang','-Wall','-Wextra','-fobjc-arc','-framework','Foundation','-framework','Metal',str(e/'gpu_event_disconnect.m'),'-o',str(target)],capture_output=True,timeout=15)
 (e/'compile.json').write_text(json.dumps({'wait':c.returncode,'stdout':c.stdout.decode(),'stderr':c.stderr.decode()},indent=2)+'\n');c.check_returncode()
 env={'sw_vers':subprocess.run(['sw_vers'],capture_output=True,check=True,timeout=5).stdout.decode(),'xcode':subprocess.run(['xcodebuild','-version'],capture_output=True,check=True,timeout=5).stdout.decode(),'machine':subprocess.run(['uname','-m'],capture_output=True,check=True,timeout=5).stdout.decode(),'helper_sha256':hashlib.sha256(target.read_bytes()).hexdigest()};(e/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
 root=e
 for mode in ["retain","drop"]:
  e=root/mode;e.mkdir(exist_ok=False)
  (e/"environment.json").write_text(json.dumps(env,indent=2)+"\n")
  for i in range(2):
   name='org.xcpreviewer.owned-event-'+uuid.uuid4().hex;domain='gui/'+str(os.getuid());job=domain+'/'+name;plist=pathlib.Path('/private/tmp/'+name+'.plist');out=pathlib.Path('/private/tmp/'+name+'.out');err=pathlib.Path('/private/tmp/'+name+'.err');loaded=False
   p=subprocess.Popen([str(target),'--parent-drop' if mode=='drop' else '--parent',name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);record={'mode':mode,'parent_pid':p.pid,'job':name,'domain':domain,'helper_sha256':env['helper_sha256']}
   try:
    plist.write_bytes(plistlib.dumps({'Label':name,'ProgramArguments':[str(target),'--peer',name,str(p.pid)],'MachServices':{name:True},'KeepAlive':False,'StandardOutPath':str(out),'StandardErrorPath':str(err)}))
    c=subprocess.run(['launchctl','bootstrap',domain,str(plist)],capture_output=True,timeout=5);record['bootstrap_wait']=c.returncode;record['bootstrap_stderr']=c.stderr.decode();c.check_returncode();loaded=True
    stdout,stderr=p.communicate(input=b'\n',timeout=15);(e/f'result-{i}.json').write_bytes(stdout);record['parent_wait']=p.returncode;record['parent_stderr']=stderr.decode()
    # This is an owned launchd job, not a user Xcode/simulator process.
    for attempt in range(20):
     c=subprocess.run(['launchctl','print',job],capture_output=True,timeout=5);s=c.stdout.decode();m=re.search(r'last exit code = (\d+)',s)
     if m and not re.search(r'\n\s*pid = \d+',s):break
     time.sleep(.05)
    record['print_wait']=c.returncode;record['last_exit_code']=int(m.group(1)) if m else None;record['peer_running_after_finish']=bool(re.search(r'\n\s*pid = \d+',s));record['program_matches']=str(target) in s
   finally:
    if p.poll() is None:p.kill();stdout,stderr=p.communicate(timeout=5);record['parent_wait']=p.returncode;record['parent_stderr']=stderr.decode();record['owned_parent_deadline_kill']=True;(e/f'result-{i}.json').write_bytes(stdout)
    if True:
     c=subprocess.run(['launchctl','bootout',job],capture_output=True,timeout=5);record['bootout_wait']=c.returncode;record['bootout_stderr']=c.stderr.decode()
    c=subprocess.run(['launchctl','print',job],capture_output=True,timeout=5);record['after_cleanup_print_wait']=c.returncode
    record['peer_stdout']=out.read_text() if out.exists() else '';record['peer_stderr']=err.read_text() if err.exists() else '';plist.unlink(missing_ok=True);out.unlink(missing_ok=True);err.unlink(missing_ok=True)
    record['plist_removed']=not plist.exists();(e/f'wait-{i}.json').write_text(json.dumps(record,indent=2)+'\n')
   assert record['parent_wait']==0 and record['last_exit_code']==0 and not record['peer_running_after_finish'] and record['bootout_wait']==0 and record['after_cleanup_print_wait']!=0,record
   print(i,'wait',record['parent_wait'],'peer',record['last_exit_code'],'service removed',flush=True)
