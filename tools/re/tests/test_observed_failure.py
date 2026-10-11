import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('failure_reader',Path(__file__).with_name('verify_observed_failure.py'))
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)


class ObservedFailureTests(unittest.TestCase):
    def test_owned_lost_observer_and_output_pressure(self):
        result=reader.verify(ROOT/'research/evidence/observed-failure-2026-10-10')
        self.assertTrue(result['unknown_cleanup_rejected'])
        self.assertEqual(result['scientific_delivery_review'],'pending')

    def test_resealed_false_release_and_bound_claims_reject(self):
        for kind in ('release','marker','settlement','output'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/observed-failure-2026-10-10',folder)
                p=folder/'controls/result.json';d=json.loads(p.read_text());loss,pressure=d['controls']
                if kind=='release':loss['record']['report']['drained']=True
                elif kind=='marker':loss['lateWritePresent']=False
                elif kind=='settlement':loss['elapsedMs']=7000
                else:pressure['record']['stdout']='x'*1025
                p.write_text(json.dumps(d));manifest=json.loads((folder/'manifest.json').read_text())
                manifest['files']['controls/result.json']={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                (folder/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError):reader.verify(folder)
