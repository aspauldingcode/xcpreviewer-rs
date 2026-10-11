import io
import json
import pathlib
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler,HTTPServer
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.core import ROOT,validate_queue
from reloop.ghidra import call
from unittest.mock import patch


class ProtocolTests(unittest.TestCase):
    def test_mcp_handshake_tools_and_invalid_experiment(self):
        with tempfile.TemporaryDirectory() as d:
            requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{}},
                      {'jsonrpc':'2.0','method':'notifications/initialized'},
                      {'jsonrpc':'2.0','id':2,'method':'tools/list'},
                      {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'re_propose','arguments':{'experiment':{'adapter':'shell'}}}}]
            p=subprocess.run([sys.executable,str(ROOT/'tools/re/agent.py'),'--state-dir',d+'/state','serve'],
                             input='\n'.join(json.dumps(x) for x in requests)+'\n',capture_output=True,text=True,timeout=15)
            self.assertEqual(p.returncode,0);responses=[json.loads(s) for s in p.stdout.splitlines()]
            self.assertEqual(len(responses),3);self.assertIn('tools',responses[1]['result']);self.assertTrue(responses[2]['result']['isError'])

    def test_seed_queue_matches_json_schema(self):
        import jsonschema
        queue=json.loads((ROOT/'research/loop/experiments.json').read_text());schema=json.loads((ROOT/'schemas/re-experiment.schema.json').read_text())
        validate_queue(queue)
        for experiment in queue['experiments']:jsonschema.validate(experiment,schema)

    def test_ghidra_health_wrapper_and_discovery(self):
        def fake(base,path,body=None,timeout=5):
            if path=='mcp/schema':return {'tools':[{'name':'vibe_health'}]}
            if path=='vibe_health':return {'ok':True,'data':{'analysis':{'ok':True}}}
            self.fail('unexpected path '+path)
        with tempfile.TemporaryDirectory() as d, patch('reloop.ghidra.http',side_effect=fake),patch('reloop.ghidra.load',return_value={}):
            result=call('vibe_health',{},pathlib.Path(d));self.assertTrue(result['engine_healthy'])

    def test_ghidra_named_http_tool_route(self):
        calls=[]
        def fake(base,path,body=None,timeout=5):
            calls.append(path)
            if path=='mcp/schema':return {'tools':[{'name':'vibe_health'},{'name':'dyld_find_cache'}]}
            if path=='vibe_health':return {'data':{'analysis':{'ok':True}}}
            if path=='dyld_find_cache':return {'ok':True,'data':{}}
            self.fail('unexpected route '+path)
        config={'ghidra_read_tools':['vibe_health','dyld_find_cache']}
        with tempfile.TemporaryDirectory() as d,patch('reloop.ghidra.http',side_effect=fake),patch('reloop.ghidra.load',return_value=config):
            self.assertTrue(call('dyld_find_cache',{},pathlib.Path(d))['tool_completed'])
        self.assertEqual(calls,['mcp/schema','vibe_health','dyld_find_cache'])

    def test_ghidra_unhealthy_is_not_success(self):
        def fake(base,path,body=None,timeout=5):
            return {'tools':[{'name':'vibe_health'}]} if path=='mcp/schema' else {'ok':True,'data':{'analysis':{'ok':False}}}
        with tempfile.TemporaryDirectory() as d,patch('reloop.ghidra.http',side_effect=fake),patch('reloop.ghidra.load',return_value={}):
            with self.assertRaises(RuntimeError):call('vibe_health',{},pathlib.Path(d))

    def test_image_mismatch_and_dimensions(self):
        from PIL import Image
        from compare_images import compare
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d);a=d/'a.png';b=d/'b.png';diff=d/'diff.png'
            Image.new('RGBA',(2,2),'white').save(a);Image.new('RGBA',(2,2),'white').save(b)
            self.assertTrue(compare(a,b,diff)['passed'])
            Image.new('RGBA',(2,2),'black').save(b);self.assertEqual(compare(a,b,diff)['changed_pixels'],4)
            Image.new('RGBA',(3,2),'white').save(b);self.assertFalse(compare(a,b,diff)['comparable'])

if __name__=='__main__':unittest.main()
