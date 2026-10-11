import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.mcp_client import Client
from reloop.bridgeprobe import summarize
from reloop.core import atomic
from reloop.planner import plan

BRIDGE='''import sys,json
for line in sys.stdin:
 m=json.loads(line)
 if 'id' not in m:continue
 method=m.get('method')
 if method=='initialize':
  print(json.dumps({'jsonrpc':'2.0','id':m['id'],'method':'ping'}),flush=True)
  reply=json.loads(sys.stdin.readline());assert reply['id']==m['id'] and reply['result']=={}
  print(json.dumps({'jsonrpc':'2.0','id':m['id'],'result':{'serverInfo':{'name':'owned-test'}}}),flush=True)
 elif method=='tools/call':
  print(json.dumps({'jsonrpc':'2.0','id':m['id'],'method':'unsupported/client/request'}),flush=True)
  reply=json.loads(sys.stdin.readline());assert reply['error']['code']==-32601
  print(json.dumps({'jsonrpc':'2.0','id':m['id'],'result':{'isError':False}}),flush=True)
'''


class BridgeProbeTests(unittest.TestCase):
    def test_planner_requires_tool_response_before_capture_and_never_requeues_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);run=root/'runs'/'owned';run.mkdir(parents=True)
            atomic(run/'manifest.json',{'sealed':True,'execution':'success','verdict':'inconclusive'})
            atomic(run/'experiment.json',{'adapter':'xcode_bridge_probe','params':{}})
            controller=SimpleNamespace(root=root,runs=root/'runs',status=lambda:{'runs':{'direct':'owned'}},verify=lambda _: {'valid':True})
            for completed,action in [(False,'inspect-xcode-permission-and-service-readiness'),(True,'attempt-owned-canvas-capture')]:
                atomic(run/'output'/'result.json',{'observations':{'initialized':True,'direct_call_completed':completed}})
                result=plan(controller)
                self.assertEqual(result['outcomes'][0]['action'],action)
                self.assertEqual(result['proposals'],[])

    def test_colliding_server_ping_and_unsupported_request_do_not_hang_client(self):
        events=[]
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/'bridge.py';path.write_text(BRIDGE)
            with (pathlib.Path(d)/'stderr').open('wb') as stderr:
                client=Client([sys.executable,str(path)],stderr,timeout=2,observer=lambda direction,message:events.append({'direction':direction,'message':message}))
                try:
                    self.assertEqual(client.initialized['serverInfo']['name'],'owned-test')
                    self.assertFalse(client.request('tools/call',{'name':'owned','arguments':{}})['isError'])
                finally:client.close()
        reverse=[e['message']['method'] for e in events if e['direction']=='in' and 'method' in e['message']]
        self.assertEqual(reverse,['ping','unsupported/client/request'])

    def test_initialize_alone_never_proves_direct_tool_route(self):
        events=[{'direction':'out','message':{'method':'initialize'}},{'direction':'out','message':{'method':'tools/call'}}]
        result=summarize(events,{'initialized':True,'error':'timeout'})
        self.assertTrue(result['initialized']);self.assertFalse(result['direct_call_completed']);self.assertFalse(result['discovery_requested'])

    def test_discovery_and_reverse_requests_remain_explicit(self):
        events=[{'direction':'out','message':{'method':'tools/list'}},{'direction':'in','message':{'method':'ping','id':7}}]
        result=summarize(events,{'completed':True});self.assertTrue(result['discovery_requested']);self.assertEqual(result['server_request_methods'],['ping'])


if __name__=='__main__':unittest.main()
