"""Synthetic expired-plan and post-prerequisite delay controls; no live APIs."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).parent
HARNESS=r'''
import contextlib,datetime,json,runpy,sys,types
from pathlib import Path
root=Path(sys.argv[1]);mode=sys.argv[2];sys.path.insert(0,str(root))
clock=lambda text:datetime.datetime.fromisoformat(text).timestamp()
import time
current=[clock('2026-10-18T17:00:00+00:00') if mode=='expired' else clock('2026-10-18T16:29:51+00:00') if mode=='reserve' else clock('2026-10-18T16:29:40+00:00')]
time.time=lambda:current[0]
counts={'render_calls':0,'snapshot_calls':0,'window_queries':0}
m=types.ModuleType('reloop.core');m.Controller=lambda:types.SimpleNamespace(lock=lambda:contextlib.nullcontext());sys.modules['reloop.core']=m
class Broker:
 def __init__(self,**kwargs):pass
 def request(self,method,params):
  if params['name']=='XcodeListWindows':
   counts['window_queries']+=1
   return {'structuredContent':{'message':'* tabIdentifier: owned, workspacePath: /Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/refresh-lifetime-20261018/PreviewLab.xcodeproj\n'}}
  if params['name']=='RenderPreview':
   counts['render_calls']+=1
   return {'structuredContent':{'previewSnapshotPath':str(root/'fake-snapshot.input'),'errors':[]}}
  raise RuntimeError('Unexpected API')
b=types.ModuleType('reloop.xcodebridge');b.BrokerClient=Broker;sys.modules['reloop.xcodebridge']=b
fake=types.ModuleType('decode');fake.decode=lambda path:{'pid':4242,'state_token_hex':'1'*32,'rgba_sha256':'0'*64,'rgba_bytes_checked':196608};sys.modules['decode']=fake
fake=types.ModuleType('identity')
def snapshot(pid,expected=None):
 counts['snapshot_calls']+=1
 current[0]=clock('2026-10-18T16:29:45+00:00') if counts['snapshot_calls']==1 else clock('2026-10-18T16:30:05+00:00')
 return {'status':'observed','root':{'pid':pid,'state':'L','identity':[1792330000,123456,'/owned/PreviewLab']}}
fake.snapshot=snapshot;fake.classify=lambda *args:(_ for _ in ()).throw(RuntimeError('Unexpected completion'));sys.modules['identity']=fake
try:runpy.run_path(str(root/'capture.py'),run_name='__main__')
except ValueError as e:print(json.dumps({**counts,'error':str(e),'capture_completed':False}))
else:raise RuntimeError('Expired plan completed')
'''
class BudgetControls(unittest.TestCase):
 def run_case(self,mode):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);pins=json.loads((P/'approved-pins.json').read_text())
   for name in [*pins,'approved-pins.json']:(root/name).write_bytes((P/name).read_bytes())
   (root/'fake-snapshot.input').write_bytes(b'not a native image; decoder mocked for budget-only control')
   p=subprocess.run([sys.executable,*(['-O'] if sys.flags.optimize else []),'-B','-c',HARNESS,str(root),mode],capture_output=True,text=True,timeout=8)
   self.assertEqual(p.returncode,0,p.stderr);return json.loads(p.stdout)
 def test_expired_plan_never_renders(self):
  v=self.run_case('expired');self.assertEqual(v['render_calls'],0);self.assertEqual(v['snapshot_calls'],0);self.assertIn('budget reserve expired',v['error'])
 def test_insufficient_reserve_never_renders(self):
  v=self.run_case('reserve');self.assertEqual(v['render_calls'],0);self.assertEqual(v['snapshot_calls'],0)
 def test_identity_delay_blocks_followup_render(self):
  v=self.run_case('delay');self.assertEqual(v['render_calls'],1);self.assertEqual(v['snapshot_calls'],2);self.assertIn('deadline expired after identity prerequisite',v['error'])
if __name__=='__main__':unittest.main()
