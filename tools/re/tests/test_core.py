import copy
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.core import Controller,atomic,canonical_hash,evaluate,execute,load,validate_queue


def experiment(key='owned-check'):
    return dict(id=key,adapter='lldb_smoke',hypothesis='Owned events are captured.',depends_on=[],resources=['debugger'],timeout_seconds=10,artifact_limit_mb=1,params={},priority=50,checks=[{'path':'events','equals':6}])


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name);self.c=Controller(root=self.root)

    def test_reject_unknown_adapter_and_parameters(self):
        e=experiment();e['adapter']='shell'
        with self.assertRaises(ValueError):validate_queue({'version':1,'experiments':[e]})
        e=experiment();e['params']={'command':'rm something'}
        with self.assertRaises(ValueError):validate_queue({'version':1,'experiments':[e]})

    def test_reject_dependency_cycles(self):
        a,b=experiment('first-check'),experiment('second-check');a['depends_on']=['second-check'];b['depends_on']=['first-check']
        with self.assertRaises(ValueError):validate_queue({'version':1,'experiments':[a,b]})

    def test_missing_observation_is_inconclusive(self):
        verdict,checks=evaluate([{'path':'events','equals':0}],{'observations':{}})
        self.assertEqual(verdict,'inconclusive');self.assertFalse(checks[0]['present'])

    def test_wrong_result_type_is_inconclusive(self):
        self.assertEqual(evaluate([{'path':'events','equals':6}],[])[0],'inconclusive')

    def test_no_boolean_integer_coercion(self):
        self.assertEqual(evaluate([{'path':'ok','equals':True}],{'observations':{'ok':1}})[0],'inconclusive')

    def test_exclusive_controller_lock(self):
        with self.c.lock():
            with self.assertRaises(RuntimeError):
                with Controller(root=self.root).lock():pass

    def test_timeout_and_process_tree_cleanup(self):
        d=self.root/'execution';d.mkdir()
        outcome=execute(['/bin/sh','-c','sleep 30 & echo $!; wait'],d,1,1024*1024)
        self.assertEqual(outcome['execution'],'timed_out')
        pid=int((d/'stdout.txt').read_text())
        # A zombie may remain briefly until reaped by its new parent, but cannot run.
        status=os.system('kill -0 '+str(pid)+' 2>/dev/null')
        if status==0:
            r=__import__('subprocess').run(['ps','-p',str(pid),'-o','stat='],capture_output=True,text=True)
            self.assertTrue(not r.stdout.strip() or r.stdout.strip().startswith('Z'))

    def test_artifact_limit(self):
        d=self.root/'execution';d.mkdir()
        r=execute([sys.executable,'-c','print("x"*100000)'],d,5,100)
        self.assertEqual(r['execution'],'artifact_limit')

    def test_sealed_artifact_tampering(self):
        run=self.c.runs/'owned-run';run.mkdir();(run/'data.txt').write_text('a')
        atomic(run/'manifest.json',{'sealed':True,'artifacts':self.c.artifacts(run)})
        self.assertTrue(self.c.verify('owned-run')['valid'])
        (run/'data.txt').write_text('b')
        self.assertFalse(self.c.verify('owned-run')['valid'])

    def test_incomplete_run_recovery(self):
        run=self.c.runs/'incomplete-run';run.mkdir();atomic(run/'manifest.json',{'sealed':False})
        with self.c.lock():self.c.recover()
        self.assertEqual(load(run/'manifest.json')['execution'],'interrupted')
        self.assertTrue(self.c.verify(run.name)['valid'])

    def test_recovery_does_not_kill_live_pid(self):
        run=self.c.runs/'incomplete-run';run.mkdir();atomic(run/'manifest.json',{'sealed':False})
        self.c.journal(run,'process_started',{'pid':os.getpid()})
        with self.assertRaises(RuntimeError):self.c.recover()
        self.assertFalse(load(run/'manifest.json')['sealed'])

    def test_identity_change_invalidates_completion(self):
        e=experiment();env={'os':'a'};run=self.c.runs/'completed-run';run.mkdir()
        atomic(run/'manifest.json',{'sealed':True,'verdict':'supports','experiment_hash':canonical_hash(e),'environment_hash':canonical_hash(env),'artifacts':[]})
        q={'version':1,'experiments':[e]};state={'runs':{e['id']:run.name}}
        self.assertEqual(self.c.ready(q,state,env),[])
        self.assertEqual(len(self.c.ready(q,state,{'os':'b'})),1)

    def test_corrupt_result_is_sealed_not_crash(self):
        def fake(argv,d,*args):
            (d/'output').mkdir();(d/'output/result.json').write_text('{')
            return {'execution':'success','exit_code':0,'duration_seconds':0}
        with patch('reloop.core.execute',side_effect=fake):m=self.c.run_one(experiment(),{'os':'owned-test'})
        self.assertTrue(m['sealed']);self.assertEqual(m['verdict'],'inconclusive')
        self.assertTrue(self.c.verify(m['run_id'])['valid'])

if __name__=='__main__':unittest.main()
