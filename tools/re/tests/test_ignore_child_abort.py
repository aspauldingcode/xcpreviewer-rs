import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_ignore_child_abort import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'research/evidence/ignore-child-abort-2026-10-14'


class IgnoreChildTests(unittest.TestCase):
    def test_measurements(self):
        self.assertEqual(hashlib.sha256((EVIDENCE/'manifest.json').read_bytes()).hexdigest(),'6cd44a4174726c56de64192ef2542dbe59a4d36d32875815f4edcdac28243ff8')
        self.assertEqual(verify(EVIDENCE)['child_signals'],[9,9])
        self.assertEqual((ROOT/'tools/re/tests/ignore_child_abort_control.js').read_bytes(),(EVIDENCE/'control.js').read_bytes())

    def test_resealed_faults(self):
        for name in ['signal','birth','receipt','prediction','wait','disposition','identity','topology','output','scope','root-exit','watcher-output','rea','status','source','abort-request','private-abort','failure-kind']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary)/'evidence'
                shutil.copytree(EVIDENCE,evidence)
                if name in ['disposition','source']:
                    path = evidence/('target.py' if name == 'disposition' else 'observed_compiler.js')
                    path.write_text(path.read_text().replace('signal.SIG_IGN','signal.SIG_DFL') if name == 'disposition' else 'invalid')
                else:
                    target = {'signal':'running-0/kernel-exit-events.json','birth':'running-0/registered.json','receipt':'running-0/result.json','prediction':'prediction.json','wait':'wait-running-0.json','identity':'running-0/result.json','topology':'running-0/result.json','output':'running-0/result.json','scope':'running-0/result.json','root-exit':'running-0/kernel-exit-events.json','watcher-output':'running-0/watcher-wait.json','rea':'rea-status.json','status':'running-0/registered.json','abort-request':'running-0/abort-request.json','private-abort':'running-0/result.json','failure-kind':'running-0/result.json'}[name]
                    path = evidence/target
                    data = json.loads(path.read_text())
                    if name == 'signal': data[1]['data'] = 15
                    elif name == 'birth': data['birth_rechecked'] = False
                    elif name == 'receipt': data['record']['report']['drained'] = False
                    elif name == 'prediction': data['child_raw_status'] = 15
                    elif name == 'identity': data['observed'][0][0]['identity'][1] = -1
                    elif name == 'topology': data['observed'][0][0]['parent'] = 1
                    elif name == 'output': data['record']['stdoutSha256'] = '0'*64
                    elif name == 'scope': data['record']['report']['scope'] = 'all processes reaped'
                    elif name == 'root-exit': data[0]['exited'] = True
                    elif name == 'watcher-output': data['stderr'] = 'failure'
                    elif name == 'rea': data['watcher']['sha256'] = '0'*64
                    elif name == 'status': data['child_status'] = 99
                    elif name == 'abort-request': data['registeredBeforeAbort'] = False
                    elif name == 'private-abort': data['record']['privateAbortRequested'] = False
                    elif name == 'failure-kind': data['record']['report']['failure'] = 'deadline'
                    else: data['code'] = 1
                    path.write_text(json.dumps(data))
                files = {str(path.relative_to(evidence)):{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in evidence.rglob('*') if path.is_file() and path.name != 'manifest.json'}
                (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(evidence)
