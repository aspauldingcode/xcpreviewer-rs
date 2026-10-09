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
from reloop.canvas import fixture_content_check, solid_color_check, require_closed_owned_workspaces


class XcodeBrokerTests(unittest.TestCase):
    def test_stale_owned_window_blocks_next_open_but_user_project_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            parent=pathlib.Path(d)/'preview-workspaces'
            owned=str(parent/'preview-owned/PreviewLab.xcodeproj')
            with self.assertRaisesRegex(RuntimeError,'Close prior owned'):
                require_closed_owned_workspaces('tabIdentifier: a, workspacePath: '+owned,parent)
            result=require_closed_owned_workspaces('tabIdentifier: user, workspacePath: '+str(pathlib.Path(d)/'User.xcodeproj'),parent)
            self.assertEqual(result['owned_workspace_windows'],0)
            self.assertEqual(require_closed_owned_workspaces('No workspace windows found',parent)['owned_workspace_windows'],0)
            with self.assertRaisesRegex(RuntimeError,'Unrecognized'):
                require_closed_owned_workspaces('new unsupported format',parent)

    def test_solid_patch_rejects_white_output_and_single_alpha_bit_change(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/'solid.png';image=Image.new('RGBA',(640,384),'white');image.save(path)
            self.assertFalse(solid_color_check([path],[2])['all_expected_colors'])
            image=Image.new('RGBA',(640,384),(255,0,0,255));image.save(path)
            self.assertTrue(solid_color_check([path],[2])['all_expected_colors'])
            image.putpixel((320,192),(255,0,0,254));image.save(path)
            result=solid_color_check([path],[2]);self.assertFalse(result['all_expected_colors'])
            self.assertEqual(result['captures'][0]['matched_pixels'],1023)

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
