"""Synthetic dependency tests plus replay of already sealed owned receipts."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE.parents[1] / "research/evidence/phase-prerequisite-candidate-2026-10-17"
sys.path.insert(0, str(HERE))
from phase_prerequisites import guarded_dispatch


def sha(data):
    return hashlib.sha256(data).hexdigest()


def row(phase):
    raw = json.dumps({'pid': 4242, 'status': 'owned_output_control'}) + '\n' if phase == 'output-valid' else ''
    err = 'owned_tree_pid:4242\n' if phase == 'output-valid' else ''
    return {'phase': phase, 'args': ['--output-control', 'output-valid'],
            'source_sha256': sha(b'owned-source'), 'binary_sha256': sha(b'owned-binary'),
            'error': None, 'record': {'report': {'kind': 'complete', 'target_code': 0,
            'failure': None, 'drained': True, 'remaining_observed': 0},
            'emergencyClosed': False, 'privateAbortRequested': False,
            'stdout': raw, 'stdoutBytes': len(raw), 'stdoutSha256': sha(raw.encode()),
            'stderr': err, 'stderrBytes': len(err), 'stderrSha256': sha(err.encode())}}


def output(value):
    raw = json.dumps(value) + '\n'
    return {'stdout': raw, 'stdoutBytes': len(raw), 'stdoutSha256': sha(raw.encode())}


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'probe.swift').write_bytes(b'owned-source')
        (self.root / 'probe').write_bytes(b'owned-binary')
        for phase in ['compile', 'output-valid']:
            self.write(phase, row(phase))
            (self.root / (phase + '-outer.json')).write_text(json.dumps({'node_exit': 0}))

    def write(self, phase, value):
        (self.root / (phase + '-record.json')).write_text(json.dumps(value))

    def reject(self):
        calls=[]
        with self.assertRaises(Exception):
            guarded_dispatch(self.root,'fixture',lambda:calls.append('fixture'))
        self.assertEqual(calls,[])

    def test_positive_dependency_order(self):
        called = []
        for phase in ['compile', 'output-valid', 'fixture']:
            self.assertEqual(guarded_dispatch(self.root, phase, lambda: called.append(phase) or 7), 7)
        self.assertEqual(called, ['compile', 'output-valid', 'fixture'])
        (self.root / 'output-valid-record.json').unlink()
        guarded_dispatch(self.root, 'output-valid', lambda: None)
        self.reject()

    def test_receipt_corruption_never_dispatches(self):
        mutations = [
            lambda x: x.update(error='timeout'),
            lambda x: x.update(phase='fixture'),
            lambda x: x.update(binary_sha256='0'*64),
            lambda x: x.update(source_sha256='0'*64),
            lambda x: x['record']['report'].update(target_code=1),
            lambda x: x['record']['report'].update(target_code=False),
            lambda x: x['record']['report'].update(drained=False),
            lambda x: x['record']['report'].update(drained=1),
            lambda x: x['record']['report'].update(remaining_observed=1),
            lambda x: x['record']['report'].update(remaining_observed=False),
            lambda x: x['record']['report'].update(kind='timeout'),
            lambda x: x['record']['report'].update(failure='late writer'),
            lambda x: x['record'].update(emergencyClosed=True),
            lambda x: x['record'].update(privateAbortRequested=True),
            lambda x: x['record'].update(stdoutBytes=True),
            lambda x: x['record'].update(stdoutSha256='0'*64),
            lambda x: x['record'].update(stderrSha256='0'*64),
            lambda x: x['record'].update(stderrBytes=True),
        ]
        for phase in ['compile', 'output-valid']:
            for index, mutate in enumerate(mutations):
                with self.subTest(phase=phase, index=index):
                    bad = row(phase);mutate(bad);self.write(phase, bad)
                    calls = []
                    with self.assertRaises(Exception):
                        guarded_dispatch(self.root, 'fixture', lambda: calls.append('fixture'))
                    self.assertEqual(calls, [])
                    self.write(phase, row(phase))

    def test_semantic_control_and_outer_failures(self):
        for value in [{'pid': True, 'status': 'owned_output_control'},
                      {'pid': 4243, 'status': 'owned_output_control'},
                      {'pid': 4242, 'status': 'failed'},
                      {'pid': 4242, 'status': 'owned_output_control', 'extra': 0}]:
            bad = row('output-valid');bad['record'].update(output(value));self.write('output-valid', bad)
            self.reject()
        self.write('output-valid', row('output-valid'))
        for phase in ['compile', 'output-valid']:
            for value in [1, False, None]:
                path=self.root/(phase+'-outer.json');path.write_text(json.dumps({'node_exit':value}))
                self.reject()
                path.write_text(json.dumps({'node_exit':0}))

    def test_missing_linked_changed_or_invalid_files(self):
        names=['compile-record.json','compile-outer.json','output-valid-record.json','output-valid-outer.json','probe.swift','probe']
        for name in names:
            path=self.root/name;before=path.read_bytes();path.unlink()
            self.reject()
            link=self.root/'target';link.write_bytes(before);path.symlink_to(link)
            self.reject()
            path.unlink();link.unlink();path.write_bytes(before)
        path=self.root/'output-valid-record.json';before=path.read_text()
        for raw in [before[:-1]+',"phase":"output-valid"}',before.replace('"error": null','"error": 1e999'),before.replace('"error": null','"error": NaN')]:
            path.write_text(raw)
            self.reject()
        path.write_text(before)
        (self.root/'probe').write_bytes(b'changed')
        self.reject()

    def test_control_args_pid_domain_and_recursive_finite_metadata(self):
        for args in [[], ['--fixture','owned-documents'], ['--output-control','output-invalid']]:
            bad=row('output-valid');bad['args']=args;self.write('output-valid',bad);self.reject()
        for pid in [1,2147483648]:
            bad=row('output-valid');bad['record'].update(output({'pid':pid,'status':'owned_output_control'}))
            err='owned_tree_pid:%d\n'%pid
            bad['record'].update(stderr=err,stderrBytes=len(err),stderrSha256=sha(err.encode()))
            self.write('output-valid',bad);self.reject()
        for err in ['', 'owned_tree_pid:4242\nowned_tree_pid:4242\n']:
            bad=row('output-valid');bad['record'].update(stderr=err,stderrBytes=len(err),stderrSha256=sha(err.encode()))
            self.write('output-valid',bad);self.reject()
        for phase in ['compile','output-valid']:
            self.write('output-valid',row('output-valid'))
            bad=row(phase);bad['diagnostic']={'nested':['OVERFLOW']}
            raw=json.dumps(bad).replace('"OVERFLOW"','1e999')
            (self.root/(phase+'-record.json')).write_text(raw);self.reject()
            self.write(phase,row(phase))
        # Finite extra diagnostic metadata is admissible; reject only unsupported numbers.
        bad=row('output-valid');bad['diagnostic']={'nested':[0,1.5,None,False]};self.write('output-valid',bad)
        called=[];guarded_dispatch(self.root,'fixture',lambda:called.append('fixture'))
        self.assertEqual(called,['fixture'])

    def test_integrated_dispatch_old_counterexample_and_fix(self):
        """Run adapter Python with fake lock and dispatch, never Node/native code."""
        old=FIXTURES/'pre-fix-execute.py';new=FIXTURES/'execute.py'
        for source,expected in [(old,True),(new,False)]:
            adapter=self.root/'execute.py';adapter.write_bytes(source.read_bytes())
            (self.root/'phase_prerequisites.py').write_bytes((HERE/'phase_prerequisites.py').read_bytes())
            (self.root/'approved-pins.json').write_text(json.dumps({n:sha((self.root/n).read_bytes()) for n in ['execute.py','phase_prerequisites.py','probe.swift']}))
            (self.root/'output-valid-record.json').unlink(missing_ok=True)
            marker=self.root/'dispatch.marker';marker.unlink(missing_ok=True)
            harness='''import sys,types,contextlib,runpy,subprocess,time
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
m=types.ModuleType('reloop.core');m.Controller=lambda:types.SimpleNamespace(lock=lambda:contextlib.nullcontext());sys.modules['reloop.core']=m
# Exercise only the Python call boundary with a fixed pre-deadline clock.
time.time=lambda:1792261547.0
def fake(*a,**k):
 (root/'dispatch.marker').write_text('synthetic dispatch only');return types.SimpleNamespace(stdout='',stderr='',returncode=0)
subprocess.run=fake
sys.argv=[str(root/'execute.py'),'fixture'];runpy.run_path(str(root/'execute.py'),run_name='__main__')
'''
            result=subprocess.run([sys.executable,*(['-O'] if sys.flags.optimize else []),'-B','-c',harness,str(self.root)],capture_output=True,text=True,timeout=5)
            self.assertEqual(marker.exists(),expected,result.stderr)
            if expected:self.assertEqual(result.returncode,0,result.stderr)
            else:self.assertNotEqual(result.returncode,0)


if __name__=='__main__':unittest.main()
