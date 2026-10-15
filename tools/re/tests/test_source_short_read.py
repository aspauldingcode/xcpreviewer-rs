import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_source_short_read import verify

ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'research/evidence/source-short-read-2026-10-14'


class SourceShortReadTests(unittest.TestCase):
    def test_real_file_measurements(self):
        self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'56003fc77eaeadfbd631fb31485239e79fc8409563bd1eee03d4590e236ed900')
        self.assertTrue(verify(E)['source_short_read_fix_qualified'])
        self.assertEqual((E/'after/source_file_loop.js').read_bytes(),(ROOT/'tools/re/reloop/source_file_loop.js').read_bytes())

    def test_resealed_faults(self):
        for fault in ['count','position','hex','published','build','oversize','event','close','worker','padding','tail','before']:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                e=Path(tmp)/'e';shutil.copytree(E,e);p=e/'after/result.json';d=json.loads(p.read_text());c=d['cases'][0]
                if fault=='count':c['reads'][0]['count']=6
                elif fault=='position':c['reads'][1]['position']=0
                elif fault=='hex':c['reads'][0]['hex']='00'
                elif fault=='published':c['published']=False
                elif fault=='build':c['builds'][0]['sha256']='0'*64
                elif fault=='oversize':d['cases'][1]['builds']=[{'bytes':7,'sha256':'0'*64}]
                elif fault=='event':d['cases'][1]['events'][0]['kind']='observed'
                elif fault=='close':c['closes']=0
                elif fault=='worker':c['status']['liveWorkers']=1
                elif fault=='before':
                    p=e/'before/result.json';d=json.loads(p.read_text());d['cases'][0]['reads'][0]['count']=202
                else:
                    p=e/'after/valid/accepted.raw';raw=bytearray(p.read_bytes());raw[52 if fault=='padding' else 16383]^=1;p.write_bytes(raw);d=None
                if d is not None:p.write_text(json.dumps(d))
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
                with self.assertRaises(AssertionError):verify(e)
