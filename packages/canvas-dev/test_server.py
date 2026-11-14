"""Behavioral tests of the source-bound server; synthetic builders are explicit."""
from pathlib import Path
import importlib.util, json, os, subprocess, sys, tempfile, threading, time, unittest
import urllib.error, urllib.request
spec=importlib.util.spec_from_file_location('canvas_dev_server',Path(__file__).with_name('server.py'))
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)


def wait_for(predicate, seconds=4):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        value=predicate()
        if value:return value
        time.sleep(.015)
    raise AssertionError('Expected observable state did not arrive')


class SyntheticBuilder(server.Session):
    def build(self,text,digest):
        if text=='bad':raise RuntimeError('Deliberate build rejection')
        data=text.encode();return {'kind':'portable','sha256':server.sha(data),'source_sha256':digest,'width':1,'height':1},data


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.source=self.root/'Preview.swift';self.source.write_text('A');self.session=SyntheticBuilder(self.source,self.root/'work',debounce=.01)
        self.addCleanup(self.tmp.cleanup);self.addCleanup(self.session.close)

    def test_error_retains_frame_and_same_source_explicit_refresh(self):
        self.session.start();first=wait_for(lambda:self.session.snapshot() if self.session.snapshot()['revision']==1 else None)
        self.source.write_text('bad');wait_for(lambda:self.session.snapshot()['state']=='error')
        self.assertEqual(self.session.snapshot()['frame'],first['frame']);self.assertEqual(self.session.snapshot()['revision'],1)
        self.source.write_text('B');wait_for(lambda:self.session.snapshot()['revision']==2)
        self.assertIsNone(self.session.snapshot()['error']);self.assertEqual(self.session.snapshot()['frame']['source_sha256'],server.sha(b'B'))
        self.session.refresh();wait_for(lambda:self.session.snapshot()['revision']==3)

    def test_superseded_build_never_replaces_accepted_frame(self):
        entered=threading.Event();release=threading.Event();calls=[]
        def build(text,digest):
            calls.append(text)
            if text=='A':entered.set();release.wait(2)
            data=text.encode();return {'sha256':server.sha(data),'source_sha256':digest},data
        self.session.build=build;self.session.start();self.assertTrue(entered.wait(2))
        self.source.write_text('B');release.set();wait_for(lambda:self.session.snapshot()['state']=='ready')
        self.assertEqual(calls,['A','B']);self.assertEqual(self.session.snapshot()['revision'],1);self.assertEqual(self.session.snapshot()['generation'],2)
        self.assertEqual(self.session.snapshot()['frame']['source_sha256'],server.sha(b'B'))

    def test_missing_file_preserves_frame_then_recovers(self):
        self.session.start();wait_for(lambda:self.session.snapshot()['revision']==1);old=self.session.snapshot()['frame']
        self.source.unlink();wait_for(lambda:self.session.snapshot()['state']=='error');self.assertEqual(self.session.snapshot()['frame'],old)
        self.source.write_text('A');wait_for(lambda:self.session.snapshot()['revision']==2)

    def test_http_save_conflict_and_cross_origin_are_rejected(self):
        http=server.make_server(self.session);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        self.addCleanup(http.server_close);self.addCleanup(http.shutdown)
        url='http://'+http.authority
        def post(text,expected,origin=None,token=None):
            headers={'Content-Type':'application/json','Origin':origin or url,'X-Canvas-Token':token or http.token}
            return urllib.request.urlopen(urllib.request.Request(url+'/api/source',data=json.dumps({'source':text,'expected_sha256':expected}).encode(),headers=headers))
        with post('B',server.sha(b'A')) as r:self.assertEqual(r.status,200)
        self.assertEqual(self.source.read_text(),'B');self.source.write_text('external')
        with self.assertRaises(urllib.error.HTTPError) as caught:post('overwrite',server.sha(b'B'))
        self.assertEqual(caught.exception.code,409);self.assertEqual(self.source.read_text(),'external')
        with self.assertRaises(urllib.error.HTTPError) as caught:post('evil',server.sha(b'external'),'http://evil.invalid')
        self.assertEqual(caught.exception.code,403);self.assertEqual(self.source.read_text(),'external')
        request=urllib.request.Request(url+'/api/session',headers={'Host':'evil.invalid'})
        with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(url+'/../README.md')
        self.assertEqual(caught.exception.code,404)

    def test_shutdown_cancels_only_its_owned_builder(self):
        errors=[]
        def run():
            try:self.session.command([sys.executable,'-c','import time; time.sleep(30)'])
            except RuntimeError as error:errors.append(str(error))
        thread=threading.Thread(target=run);self.session.thread=thread;thread.start()
        wait_for(lambda:self.session.child);child=self.session.child;self.session.close();thread.join(2)
        self.assertFalse(thread.is_alive());self.assertIsNotNone(child.poll());self.assertEqual(errors,['Preview server stopped'])
        with self.assertRaisesRegex(RuntimeError,'stopped'):self.session.command([sys.executable,'-c','raise Exception("must not run")'])

if __name__=='__main__':unittest.main()
