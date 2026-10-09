import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.xcodebridge import BrokerClient, validate_request
from reloop.canvas import fixture_content_check


class XcodeBrokerTests(unittest.TestCase):
    def test_window_chrome_changes_do_not_satisfy_owned_content_gate(self):
        from PIL import Image, ImageDraw
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/'window.png';image=Image.new('RGBA',(640,384),'white')
            draw=ImageDraw.Draw(image);draw.rectangle((0,0,639,63),fill='black');image.save(path)
            result=fixture_content_check([path]);self.assertFalse(result['all_content_nonblank'])
            self.assertEqual(result['captures'][0]['interior_ink_pixels'],0)
            draw.rectangle((100,180,200,190),fill='black');image.save(path)
            self.assertTrue(fixture_content_check([path])['all_content_nonblank'])

    def test_reject_arbitrary_methods_and_tools(self):
        for request in [{'method':'shell'}, {'method':'tools/call','params':{'name':'XcodeWrite'}}]:
            with self.assertRaises(ValueError):validate_request(request)
        self.assertEqual(validate_request({'method':'tools/call','params':{'name':'RenderPreview'}})[0],'tools/call')

    def test_reject_shared_endpoint(self):
        with tempfile.TemporaryDirectory() as d:
            os.chmod(d,0o755)
            with self.assertRaises(RuntimeError):BrokerClient(d)

    def test_independent_callers_retain_one_upstream_process_and_session(self):
        with tempfile.TemporaryDirectory() as d:
            directory=pathlib.Path(d);owned=directory/'owned.py'
            owned.write_text('''import json,sys
count=0
for line in sys.stdin:
 m=json.loads(line)
 if 'id' not in m: continue
 count+=1
 print(json.dumps({'jsonrpc':'2.0','id':m['id'],'result':{'count':count}}),flush=True)
''')
            command='from reloop.xcodebridge import serve;serve('+repr(d)+',command='+repr([sys.executable,str(owned)])+')'
            env=dict(os.environ,PYTHONPATH=str(pathlib.Path(__file__).resolve().parents[1]))
            with (directory/'test.log').open('wb') as log:
                process=subprocess.Popen([sys.executable,'-c',command],env=env,stdout=log,stderr=log)
                try:
                    deadline=time.monotonic()+5
                    while not (directory/'broker.sock').exists() and time.monotonic()<deadline:
                        if process.poll() is not None:self.fail((directory/'test.log').read_text())
                        time.sleep(.05)
                    first=BrokerClient(d,timeout=2);metadata=first.metadata
                    self.assertEqual(first.request('tools/list',{})['count'],2);first.close()
                    second=BrokerClient(d,timeout=2)
                    self.assertEqual(second.metadata['pid'],metadata['pid'])
                    self.assertEqual(second.metadata['session_id'],metadata['session_id'])
                    self.assertEqual(second.request('tools/list',{})['count'],3);second.close()
                    self.assertIsNone(process.poll())
                finally:
                    if process.poll() is None:process.terminate()
                    process.wait(timeout=5)
            self.assertFalse((directory/'broker.sock').exists())


if __name__=='__main__':unittest.main()
