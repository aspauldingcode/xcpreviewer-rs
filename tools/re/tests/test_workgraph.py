import json,pathlib,tempfile,unittest
from reloop.workgraph import build,topology

class FakeController:
    def __init__(self,root):self.root=root;self.runs=root/'runs';self.good=True
    def verify(self,rid,anchor):return {'valid':self.good,'external_anchor_matches':self.good and anchor=='trusted'}

class WorkGraphTests(unittest.TestCase):
    def fixture(self,root):
        c=FakeController(root);p=c.runs/'r';p.mkdir(parents=True);(p/'manifest.json').write_text(json.dumps(dict(sealed=True,execution='success',verdict='supports',artifacts=[{'path':'coverage.json'}])))
        roadmap={'issues':{'A':dict(depends_on_ids=[],milestone=1,url='a'),'B':dict(depends_on_ids=['A'],milestone=1,url='b')}}
        policy={'acceptance_attestations':{},'research_tasks':[dict(id='research-b',issue='B',scope='owned',priority=100,requires_runs=['r'])]}
        checkpoint={'recent_evidence':[dict(run_id='r',manifest_sha256='trusted')],'blocked_tracks':[]}
        return c,roadmap,policy,checkpoint
    def test_scoped_success_keeps_delivery_open_but_research_ready(self):
        with tempfile.TemporaryDirectory() as d:
            c,r,p,q=self.fixture(pathlib.Path(d));g=build(c,r,p,q)
            self.assertFalse(g['milestone1_complete']);self.assertEqual(g['next_task'],'research-b');self.assertEqual(g['research_frontier'][0]['acceptance_dependencies_unmet'],['A'])
    def test_cycles_dangling_and_duplicates_rejected(self):
        for issues in ({'A':{'depends_on_ids':['A']}},{'A':{'depends_on_ids':['missing']}},{'A':{'depends_on_ids':['B','B']},'B':{'depends_on_ids':[]}}):
            with self.assertRaises(ValueError):topology(issues)
    def test_blocked_and_unanchored_work_not_selected(self):
        with tempfile.TemporaryDirectory() as d:
            c,r,p,q=self.fixture(pathlib.Path(d));p['research_tasks'][0]['blocked_track']='attach';q['blocked_tracks']=[dict(track='attach',retry_requires='changed method')]
            self.assertIsNone(build(c,r,p,q)['next_task']);q['blocked_tracks']=[];c.good=False
            g=build(c,r,p,q);self.assertIsNone(g['next_task']);self.assertEqual(g['quarantined_runs'],['r'])
            c.good=True;q['recent_evidence']=[];self.assertIsNone(build(c,r,p,q)['next_task'])
    def test_explicit_acceptance_needs_sealed_coverage_and_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            c,r,p,q=self.fixture(pathlib.Path(d));a=dict(contract_reviewed=True,coverage_path='coverage.json',runs=['r']);p['acceptance_attestations']={'B':a}
            self.assertFalse(build(c,r,p,q)['milestone1_complete']);p['acceptance_attestations']['A']=a
            self.assertTrue(build(c,r,p,q)['milestone1_complete']);p['acceptance_attestations']['A']={**a,'coverage_path':'unsealed.json'}
            self.assertFalse(build(c,r,p,q)['milestone1_complete'])
    def test_completed_research_skipped_without_completing_delivery(self):
        with tempfile.TemporaryDirectory() as d:
            c,r,p,q=self.fixture(pathlib.Path(d));p['research_tasks'][0]['completion_runs']=['r'];(c.runs/'r'/'experiment.json').write_text(json.dumps({'id':'research-b'}))
            g=build(c,r,p,q);self.assertIsNone(g['next_task']);self.assertEqual(g['research_frontier'][0]['state'],'complete');self.assertFalse(g['milestone1_complete'])
            (c.runs/'r'/'experiment.json').write_text(json.dumps({'id':'unrelated'}));self.assertEqual(build(c,r,p,q)['next_task'],'research-b')
