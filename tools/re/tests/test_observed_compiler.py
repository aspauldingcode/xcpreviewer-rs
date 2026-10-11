import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('observed_reader',Path(__file__).with_name('verify_observed_compiler.py'))
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)


class ObservedCompilerTests(unittest.TestCase):
    def test_native_controls_and_every_fresh_allocation_byte(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/observed-compiler-2026-10-10')['fresh_allocation_bytes'],49152)

    def test_resealed_cleanup_status_and_padding_mutants_reject(self):
        for kind in ('drain','remaining','status','padding'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/observed-compiler-2026-10-10',folder)
                name='fresh/result/0-frame.raw' if kind=='padding' else 'controls/result.json'
                p=folder/name
                if kind=='padding':
                    data=bytearray(p.read_bytes());data[-1]^=1;p.write_bytes(data)
                else:
                    d=json.loads(p.read_text());report=d['controls'][1]['record']['report']
                    if kind=='drain':report['drained']=False
                    elif kind=='remaining':report['remaining_observed']=1
                    else:report['target_code']=0
                    p.write_text(json.dumps(d))
                manifest=json.loads((folder/'manifest.json').read_text())
                manifest['files'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                (folder/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError):reader.verify(folder)
