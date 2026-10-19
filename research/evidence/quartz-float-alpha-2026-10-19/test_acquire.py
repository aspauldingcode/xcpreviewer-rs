"""Synthetic receipt gate tests; no native execution."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import acquire
import compare as c
from test_compare import Controls

ROOT=Path(__file__).resolve().parent
OLD=Path('/Users/8amps/xcpreviewer-rs/research/evidence/quartz-alpha-transfer-2026-10-19')
class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
        for name in c.parsed((ROOT/'approved-pins.json').read_text()):shutil.copy2(ROOT/name,self.p/name)
        shutil.copy2(ROOT/'approved-pins.json',self.p/'approved-pins.json')
        controls=Controls();controls.setUp();self.addCleanup(controls.tmp.cleanup)
        shutil.copytree(controls.root,self.p/'owned-documents')
        rows=controls.rows
        source=c.digest((self.p/'probe.c').read_bytes());binary='a'*64
        execution='/private/tmp/quartz-float-alpha-20261019'
        for i,phase in enumerate(['compile','output-valid','fixture']):
            stdout='' if phase=='compile' else json.dumps({'pid':100,'status':'owned_output_control'})+'\n' if phase=='output-valid' else ''.join(json.dumps(row)+'\n' for row in rows)
            stderr='' if phase=='compile' else 'owned_tree_pid:100\n'
            args=['clang','-framework','CoreGraphics','-framework','CoreFoundation',execution+'/probe.c','-o',execution+'/probe'] if phase=='compile' else ['--output-control','output-valid'] if phase=='output-valid' else ['--fixture',execution+'/owned-documents']
            record={'report':{'kind':'complete','target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stdout':stdout,'stderr':stderr,'stdoutBytes':len(stdout.encode()),'stdoutSha256':c.digest(stdout.encode()),'stderrBytes':len(stderr.encode()),'stderrSha256':c.digest(stderr.encode())}
            row={'phase':phase,'command':'/usr/bin/xcrun' if phase=='compile' else execution+'/probe','args':args,'source_sha256':source,'binary_sha256':binary,'error':None,'record':record}
            self.write(phase+'-record.json',row);self.write(phase+'-outer.json',{'node_exit':0})
            self.write(phase+'-started.json',{'phase':phase,'started_at':'2026-10-19T16:44:0%d+00:00'%i,'deadline_utc':'2026-10-19T16:48:00Z'})
        self.write('completed.json',{'completed_at':'2026-10-19T16:44:03+00:00','deadline_utc':'2026-10-19T16:48:00Z'})
        self.write('rea-identity.json',{'owned_binary_sha256':binary,'closed':True,'architecture':'arm64','server':{'version':'6.2.0','command_path':'/Users/8amps/xcpreviewer-rs/research/build/rea/node_modules/rea-agents/scripts/rea.mjs'}})
    def write(self,name,value): (self.p/name).write_text(json.dumps(value))
    def run_case(self): return acquire.observed(self.p,OLD)
    def test_synthetic_positive(self):
        value=self.run_case();self.assertTrue(value['native_acquisition_qualified']);self.assertTrue(value['linear_identity_control']);self.assertFalse(value['canvas_qualified'])
    def test_bad_receipts(self):
        q=self.p/'fixture-record.json';original=q.read_bytes()
        for field,value in [('target_code',False),('remaining_observed',False),('drained',False),('target_code',7)]:
            with self.subTest(field=field,value=value):
                row=json.loads(original);row['record']['report'][field]=value;self.write(q.name,row)
                with self.assertRaises(ValueError):self.run_case()
        q.write_bytes(original)
        (self.p/'output-valid-outer.json').unlink()
        with self.assertRaises((ValueError,FileNotFoundError)):self.run_case()
    def test_source_and_chronology(self):
        q=self.p/'completed.json';row=json.loads(q.read_text());row['completed_at']='2026-10-19T16:49:00+00:00';self.write(q.name,row)
        with self.assertRaises(ValueError):self.run_case()
        row['completed_at']='2026-10-19T16:44:03+00:00';self.write(q.name,row)
        with (self.p/'probe.c').open('a') as f:f.write('\n// changed\n')
        with self.assertRaises(ValueError):self.run_case()
    def test_wrong_command_and_rea(self):
        q=self.p/'fixture-record.json';original=q.read_bytes();row=json.loads(original);row['args']=['--fixture','/unowned'];self.write(q.name,row)
        with self.assertRaises(ValueError):self.run_case()
        q.write_bytes(original);row=json.loads((self.p/'rea-identity.json').read_text());row['closed']=False;self.write('rea-identity.json',row)
        with self.assertRaises(ValueError):self.run_case()
if __name__=='__main__':unittest.main()
