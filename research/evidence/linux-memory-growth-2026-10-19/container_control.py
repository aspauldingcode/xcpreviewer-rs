"""Bounded cleanup through a caller-supplied pinned Docker context; no VM actions."""
from phase_prerequisites import require,integer

def cleanup(call,plan,sink):
 inspect=call(['inspect','--format','{{index .Config.Labels "xcpreviewer.owner"}}',plan['name']])
 report={'owned_name':plan['name'],'owner_label':plan['owner'],'inspect_exit':inspect.returncode,'inspect_owner':inspect.stdout.strip() if inspect.returncode==0 else None,'cleanup_exit':None,'remaining_exit':None,'remaining':None}
 if inspect.returncode==0:
  if inspect.stdout.strip()!=plan['owner']:
   report['failure']='ownership mismatch';sink(report);require(False,'Refusing cleanup of unowned container')
  report['cleanup_exit']=call(['rm','-f',plan['name']]).returncode
 remaining=call(['ps','-a','--filter','name=^/'+plan['name']+'$','--format','{{.Names}}'])
 report.update(remaining_exit=remaining.returncode,remaining=remaining.stdout.strip());sink(report)
 require(integer(report['remaining_exit'],0) and report['remaining']=='' and (report['cleanup_exit'] is None or integer(report['cleanup_exit'],0)),'Owned Linux container cleanup unverified')
 return report

def docker_command(plan):
 require(type(plan['owner']) is str and len(plan['owner'])==32 and all(c in '0123456789abcdef' for c in plan['owner']),'owner nonce')
 require(plan['name']=='xcpreviewer-memory-'+plan['owner'][:12] and plan['context']=='colima','owned name/context')
 require(integer(plan['uid']) and integer(plan['gid']) and plan['uid']>=0 and plan['gid']>=0,'uid/gid')
 stage='/Users/8amps/xcpreviewer-rs/research/build/linux-memory-growth-'+plan['owner']
 return ['docker','--context','colima','run','--rm','--pull','never','--name',plan['name'],'--label','xcpreviewer.owner='+plan['owner'],'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64','--memory','256m','--cpus','1','--user','%d:%d'%(plan['uid'],plan['gid']),'--env','PYTHONPATH=/runtime','--env','PYTHONDONTWRITEBYTECODE=1','--mount','type=bind,src=%s,dst=/experiment,readonly'%stage,'--mount','type=bind,src=%s,dst=/runtime,readonly'%(plan['runtime_root']+'/package'),'--mount','type=bind,src=%s,dst=/out'%(stage+'/owned-output'),'--entrypoint','/app/.venv/bin/python3',plan['image'],'-B','/experiment/runner.py']
