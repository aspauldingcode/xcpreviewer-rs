import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from verify_surface_partial_right import verify

ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'research/evidence/surface-partial-cleanup-2026-10-14'


class SurfacePartialRightTests(unittest.TestCase):
    def test_native_invalid_destination(self):
        self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'d8c5acef6c6154e836c639869591d0e18d226576cc7bcbf9b9cf6ce6488f1d76')
        self.assertTrue(verify(E)['partial_descriptor_failure_qualified'])
        self.assertEqual((E/'surface_partial_right.c').read_bytes(),(ROOT/'tools/re/surface_partial_right.c').read_bytes())

    def test_resealed_faults(self):
        faults = {'send_code':0,'first_disposition':19,'second_disposition':19,'remote_type':17,'before_original':1,'before_returned':1,'after_returned':1,'invalid_type_after':0,'remaining_send_refs':1,'explicit_cleanup':False,'padding':None,'tail':None}
        for fault, value in faults.items():
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                e = Path(temporary)/'e';shutil.copytree(E,e)
                p = e/'move/stdout.jsonl';r = json.loads(p.read_text())
                if fault in ['padding','tail']:
                    p = e/'move/alias-after-cleanup.bin';raw = bytearray(p.read_bytes());raw[68 if fault == 'padding' else 16383] ^= 1;p.write_bytes(raw)
                else:
                    r[fault] = value;p.write_text(json.dumps(r)+'\n')
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name != 'manifest.json'}}))
                with self.assertRaises(AssertionError): verify(e)

    def test_additional_admission_faults(self):
        for fault in ['wait_code', 'endpoint_refs', 'padding', 'tail']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                e = Path(temporary)/'e';shutil.copytree(E,e)
                if fault == 'wait_code':
                    (e/'move/wait.json').write_text(json.dumps({'code':7,'timeout':False}))
                elif fault == 'endpoint_refs':
                    p = e/'move/stdout.jsonl';row = json.loads(p.read_text())
                    row['after_endpoint'] = 2;p.write_text(json.dumps(row)+'\n')
                else:
                    p = e/'move/alias-after-cleanup.bin';raw = bytearray(p.read_bytes())
                    raw[68 if fault == 'padding' else 16383] ^= 1;p.write_bytes(raw)
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name != 'manifest.json'}}))
                with self.assertRaises(AssertionError): verify(e)

    def test_optimized_admission(self):
        tests = ['test_native_invalid_destination','test_resealed_faults','test_additional_admission_faults','test_typed_admission_faults']
        result = subprocess.run([sys.executable,'-O','-m','unittest',*[__name__+'.SurfacePartialRightTests.'+name for name in tests]],cwd=Path(__file__).parent,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_typed_admission_faults(self):
        faults = ['pid_float','returned_name_float','second_name_float','endpoint_bool','remaining_refs_bool','compile_code_bool','wait_code_bool','timeout_int','send_code_float','stride_float']
        for fault in faults:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                e = Path(temporary)/'e';shutil.copytree(E,e)
                p = e/'move/stdout.jsonl';row = json.loads(p.read_text())
                if fault.endswith('_float'):
                    key = fault[:-6];row[key] = float(row[key]);p.write_text(json.dumps(row)+'\n')
                elif fault == 'endpoint_bool':
                    row['after_endpoint'] = True;p.write_text(json.dumps(row)+'\n')
                elif fault == 'remaining_refs_bool':
                    row['remaining_send_refs'] = False;p.write_text(json.dumps(row)+'\n')
                elif fault == 'compile_code_bool':
                    (e/'compile-wait.json').write_text(json.dumps({'code':False}))
                elif fault == 'wait_code_bool':
                    (e/'move/wait.json').write_text(json.dumps({'code':False,'timeout':False}))
                else:
                    (e/'move/wait.json').write_text(json.dumps({'code':0,'timeout':0}))
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name != 'manifest.json'}}))
                with self.assertRaises(AssertionError): verify(e)
