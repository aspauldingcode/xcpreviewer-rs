"""Deterministic guard contract controls; mocked process/observer, not native evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('diagnostic_anchor', HERE/'observed_group_anchor.py')
anchor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anchor)
class StopLoop(BaseException): pass
class GuardControls(unittest.TestCase):
    def run_case(self, kind):
        writes=[];signals=[];calls=[];state={'samples':0};buffers={};write_calls=[]
        root=dict(pid=100,parent=99,group=99,state='L',identity=[10,20,'/owned/a'])
        child=dict(pid=101,parent=100,group=99,state='L',identity=[11,21,'/owned/child'])
        class Target:
            pid=100
            def poll(self):
                n=state['samples']
                if kind in ('live_missing','helper_failure','known_missing','large_missing','malformed','partial_write','zero_write'):return None
                if kind=='genuine_exit':return 0 if n>=1 else None
                if kind=='exec_transition':return 0 if n>=2 else None
                return 0 if n>=1 else None
            def wait(self, timeout):
                self.wait_called=True
                return 0
        target=Target()
        def observe(argv,**kwargs):
            calls.append(argv);state['samples']+=1;n=state['samples']
            if kind=='helper_failure':raise subprocess.CalledProcessError(2,argv)
            if kind=='malformed':return subprocess.CompletedProcess(argv,0,stdout=b'invalid',stderr=b'')
            if kind=='large_missing':return subprocess.CompletedProcess(argv,0,stdout=b' '*40000+b'[]',stderr=b'')
            if kind in ('live_missing','genuine_exit','partial_write','zero_write'):rows=[]
            elif kind=='known_missing':rows=[root] if n==1 else []
            elif kind=='exec_transition':
                rows=[dict(root,identity=[10,20,'/owned/a' if n==1 else '/owned/b'])] if n<=2 else []
            elif n==1:rows=[root,child]
            elif n==2:rows=[child if kind=='descendant' else dict(child,identity=[999,21,'/owned/other'])]
            else:rows=[]
            return subprocess.CompletedProcess(argv,0,stdout=json.dumps(rows).encode(),stderr=b'')
        def write(fd, data):
            write_calls.append(fd)
            if fd==2 and kind=='zero_write':return 0
            n=max(1,len(data)//2) if fd==2 and kind=='partial_write' and write_calls.count(2)==1 else len(data)
            buffers[fd]=buffers.get(fd,b'')+data[:n]
            return n
        def sleep(seconds):
            if seconds==3600:raise StopLoop()
        with tempfile.TemporaryDirectory() as directory:
            helper=Path(directory)/'helper';helper.write_bytes(b'owned mock observer')
            argv=['anchor',str(helper),hashlib.sha256(helper.read_bytes()).hexdigest(),'1000','/owned/target']
            with patch.object(anchor.sys,'argv',argv),patch.object(anchor.os,'set_blocking'),patch.object(anchor.os,'read',return_value=b''),patch.object(anchor.os,'write',side_effect=write),patch.object(anchor.os,'kill',side_effect=lambda pid,sig:signals.append((pid,sig))),patch.object(anchor.subprocess,'Popen',return_value=target),patch.object(anchor.subprocess,'run',side_effect=observe),patch.object(anchor.time,'sleep',side_effect=sleep):
                with self.assertRaises(StopLoop):anchor.main()
        for fd,data in buffers.items():
            writes.extend((fd,json.loads(line)) for line in data.splitlines())
        return writes,signals,calls,target
    def test_live_root_omission_stays_fatal_with_complete_small_diagnostic(self):
        writes,signals,calls,target=self.run_case('live_missing')
        diagnostic=[v for fd,v in writes if fd==2][0]
        self.assertEqual(diagnostic['poll_before'],None);self.assertEqual(diagnostic['poll_after'],None)
        self.assertTrue(diagnostic['helper_stdout_complete']);self.assertEqual(diagnostic['helper_stdout_prefix'],'[]')
        self.assertEqual(diagnostic['helper_args'],['100'])
        report=[v for fd,v in writes if fd==3 and v['kind']=='complete'][0]
        self.assertFalse(report['drained']);self.assertIsNone(report['target_code']);self.assertEqual(signals,[])
    def test_known_identity_missing_remains_fatal(self):
        writes,signals,_,_=self.run_case('known_missing')
        diagnostic=[v for fd,v in writes if fd==2][0]
        self.assertEqual(diagnostic['known_target_identity'],[10,20,'/owned/a'])
        self.assertEqual(diagnostic['observations'],1)
        self.assertFalse([v for fd,v in writes if fd==3 and v['kind']=='complete'][0]['drained'])
        self.assertEqual(signals,[])
    def test_large_response_is_explicitly_incomplete_and_bounded(self):
        writes,_,_,_=self.run_case('large_missing')
        diagnostic=[v for fd,v in writes if fd==2][0]
        self.assertFalse(diagnostic['helper_stdout_complete'])
        self.assertEqual(diagnostic['helper_stdout_bytes'],40002)
        self.assertEqual(len(diagnostic['helper_stdout_prefix']),32768)
        self.assertEqual(diagnostic['helper_stdout_sha256'],hashlib.sha256(b' '*40000+b'[]').hexdigest())
        self.assertLessEqual(len(json.dumps(diagnostic).encode()),262144)
    def test_malformed_helper_data_remains_fatal(self):
        writes,signals,_,_=self.run_case('malformed')
        report=[v for fd,v in writes if fd==3 and v['kind']=='complete'][0]
        self.assertFalse(report['drained']);self.assertEqual(signals,[])
    def test_partial_diagnostic_write_completes_without_success(self):
        writes,signals,_,_=self.run_case('partial_write')
        self.assertEqual(len([v for fd,v in writes if fd==2]),1)
        self.assertFalse([v for fd,v in writes if fd==3 and v['kind']=='complete'][0]['drained'])
        self.assertEqual(signals,[])
    def test_zero_write_fails_closed(self):
        writes,signals,_,_=self.run_case('zero_write')
        report=[v for fd,v in writes if fd==3 and v['kind']=='complete'][0]
        self.assertFalse(report['drained']);self.assertIn('no valid progress',report['failure'])
        self.assertEqual(signals,[])
    def test_genuine_exit_uses_actual_wait_and_no_identity_invention(self):
        writes,signals,_,target=self.run_case('genuine_exit')
        self.assertTrue(target.wait_called);self.assertEqual(signals,[])
        report=[v for fd,v in writes if fd==3 and v['kind']=='complete'][0]
        self.assertTrue(report['drained']);self.assertEqual(report['target_code'],0)
    def test_exec_transition_history_observed(self):
        writes,_,_,_=self.run_case('exec_transition')
        paths=[row['identity'][2] for fd,v in writes if fd==3 and v['kind']=='observed' for row in v['rows']]
        self.assertEqual(paths,['/owned/a','/owned/b'])
    def test_helper_failure_remains_unverified_without_signal(self):
        writes,signals,_,_=self.run_case('helper_failure')
        report=[v for fd,v in writes if fd==3 and v['kind']=='complete'][0]
        self.assertFalse(report['drained']);self.assertIn('CalledProcessError',report['failure']);self.assertEqual(signals,[])
    def test_observed_descendant_signal_requires_same_identity(self):
        _,signals,_,_=self.run_case('descendant');self.assertEqual(signals,[(101,signal.SIGTERM)])
        _,signals,_,_=self.run_case('reused_pid');self.assertEqual(signals,[])
if __name__=='__main__':unittest.main()
