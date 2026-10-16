"""Run current disk UCU against an owned non-UI peer; never real axbridge."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
repo=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(repo/'tools/re'))
from reloop.core import Controller
root=Path(__file__).resolve().parent
binary=Path('/Users/8amps/.local/bin/ucu')
expected='40d62e6f51cebbc9d32578d166c79a745d193bd7e3c6a19ff31cdddb6a872894'
if hashlib.sha256(binary.read_bytes()).hexdigest()!=expected:raise ValueError('Binary pin changed')
mock=root/'mock_bridge.py';mock.chmod(0o700)
mock_sha=hashlib.sha256(mock.read_bytes()).hexdigest()
run=root/'owned-run';run.mkdir(mode=0o700,exist_ok=False)
requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'owned-routing-control','version':'1'}}}]
for i,op in enumerate(['click','press','CLICK'],2):
 requests.append({'jsonrpc':'2.0','id':i,'method':'tools/call','params':{'name':'computer_act','arguments':{'target':'ax-owned-mock','op':op,'ref':'ax:0.0','label':'Owned sentinel '+op}}})
payload=''.join(json.dumps(q)+'\n' for q in requests)
# Explicit peer override and isolated data directory; never inherit browser target.
env={k:v for k,v in os.environ.items() if not k.startswith('PYTHON')}
env.update(UCU_AXBRIDGE=str(mock),UCU_DATA_DIR=str(run/'mock-data'),UCU_BROWSER_PROFILE=str(run/'mock-profile'),ROUTING_RECORD=str(run/'mock-requests.jsonl'))
with Controller().lock():
 start=time.monotonic();p=subprocess.Popen([str(binary),'mcp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True,text=True)
 try:out,err=p.communicate(payload,timeout=20)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate(timeout=5)
  (root/'failed-timeout.json').write_text(json.dumps({'pid':p.pid,'returncode':p.returncode,'stdout':out,'stderr':err,'cleanup':'Owned group fallback; no successful release claim'}))
  raise
 if len(out.encode())+len(err.encode())>262144:raise ValueError('Post-exit output admission cap exceeded; capture itself time-bounded only')
 (root/'stdio.json').write_text(json.dumps({'requests':requests,'stdout':out,'stderr':err,'returncode':p.returncode,'seconds':time.monotonic()-start},indent=2)+'\n')
 if p.returncode!=0:raise ValueError('UCU nonzero exit')
 rows=[json.loads(s) for s in out.splitlines()];peer=[json.loads(s) for s in (run/'mock-requests.jsonl').read_text().splitlines()]
 if [x.get('id') for x in rows]!=[1,2,3,4]:raise ValueError('Missing or extra response')
 if [(x['request'].get('id'),x['request'].get('expect')) for x in peer]!=[(1,'Owned sentinel click'),(2,'Owned sentinel press'),(3,'Owned sentinel CLICK')]:raise ValueError('Peer/request binding mismatch')
 if hashlib.sha256(mock.read_bytes()).hexdigest()!=mock_sha:raise ValueError('Mock changed')
 if [x['request'].get('op') for x in peer]!=['PRESS','PRESS','CLICK']:raise ValueError('Predicted dispatch falsified; retain output')
 if any(x['request'].get('app')!='ax-owned-mock' or x['request'].get('method')!='act' for x in peer):raise ValueError('Unexpected peer invocation')
 if [x['result'].get('isError') for x in rows[1:]]!=[True,True,False]:raise ValueError('Unexpected MCP result')
 if rows[-1]['result'].get('structuredContent',{}).get('result')!={'mock_only':True,'forwarded':'CLICK'}:raise ValueError('Missing owned mock acknowledgement')
 # No native AX bridge launched. Check only exact recorded mock PIDs for absence;
 # kill(0) is an availability observation, not a native wait/reap proof.
 absent=[]
 for pid in sorted({x['pid'] for x in peer}):
  for _ in range(20):
   try:os.kill(pid,0)
   except ProcessLookupError:absent.append(pid);break
   time.sleep(.05)
 if len(absent)!=len({x['pid'] for x in peer}):raise ValueError('Mock peer still observable; no success admission')
 result={'binary_sha256':expected,'mock_sha256':mock_sha,'root_wait_status':p.returncode,'observed_dispatch':['PRESS','PRESS','CLICK'],'mcp_errors':[True,True,False],'peer_pids_absent':absent,'native_ui_executed':False,'grade':'actual-UCU-binary-with-mock-AX-peer','limitations':['No live MCP instance attribution','No real Swift axbridge execution','No real element/window binding','Peer absence is not wait/reap proof','communicate capture time-bounded;256KiB cap checked only after exit','Binary-to-current-source reproducibility not established']}
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
