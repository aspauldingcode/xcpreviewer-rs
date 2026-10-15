import copy
import json
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from canvas_graph import ROOT, read, sha, validate, plan, export_handoff
from reloop.graphloop import run


class CanvasGraphTests(unittest.TestCase):
    def test_real_pilot_and_role_frontier(self):
        graph=read(ROOT/'research/loop/canvas-graph.json')
        self.assertEqual(validate(ROOT,graph)['entities'],15)
        result=plan(ROOT,graph)
        self.assertEqual(result['next_task'],'provenance-inventory')
        self.assertFalse(result['milestone1_complete']);self.assertFalse(result['milestone2_complete'])
        self.assertTrue(all(t['state']=='blocked' for t in result['tasks'] if t['kind']=='implementation'))
        self.assertIsNone(plan(ROOT,graph,'clean-implementer')['next_task'])

    def test_scope_fusion_and_relation_types_rejected(self):
        graph=read(ROOT/'research/loop/canvas-graph.json')
        for fault in ['duplicate','domain','provenance','cycle','grade','budget']:
            with self.subTest(fault=fault):
                g=copy.deepcopy(graph)
                if fault=='duplicate':g['knowledge']['nodes'].append({**g['knowledge']['nodes'][0],'id':'different-id'})
                elif fault=='domain':g['knowledge']['edges'][0]['relation']='RELEASES'
                elif fault=='provenance':g['knowledge']['nodes'][0]['provenance']['sha256']='0'*64
                elif fault=='cycle':g['tasks'][0]['requires']=[g['tasks'][0]['id']]
                elif fault=='grade':g['knowledge']['nodes'][-5]['grade']='native-correlated'
                else:g['tasks'][0]['budget']['native_jobs']=100
                with self.assertRaises(ValueError):validate(ROOT,g)

    def fixture(self,root):
        (root/'ontology.json').write_text(json.dumps({'entity_types':{'Evidence':'proof'},'relations':{}}))
        (root/'source.md').write_text('Owned public observation')
        graph={'ontology':'ontology.json','knowledge':{'nodes':[{'id':'e','type':'Evidence','semantic_key':'one','scope':'native boundary','target_version':'one','grade':'native-correlated','provenance':{'path':'source.md','sha256':sha(root/'source.md'),'locator':'whole','extracted_at':'2026-10-15T00:00:00Z','confidence':'observed'}}],'edges':[]},'tasks':[{'id':'native','role':'evidence-verifier','kind':'verification','requires':[],'priority':1,'issue_ids':['R1'],'scope':'native boundary','grade_required':'native-correlated','acceptance_checks':['wait','bytes'],'outputs':['output.json'],'milestone_gate':1,'budget':{'rounds':1,'native_jobs':0,'seconds_per_native_job':15,'artifact_bytes':1024}}],'attestations':{}}
        (root/'output.json').write_text('{}')
        report={'task':'native','verdict':'accepted','producer_context':'producer','reviewer_context':'reviewer','grade':'native-correlated','scope':'native boundary','checks':{'wait':True,'bytes':True},'artifacts':[{'path':'output.json','sha256':sha(root/'output.json')}]}
        return graph,report

    def test_acceptance_requires_independent_scoped_complete_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);graph,report=self.fixture(root)
            for fault in ['same-context','owned-grade','missing-check','missing-artifact','wrong-output','wrong-scope','changed-output']:
                with self.subTest(fault=fault):
                    r=copy.deepcopy(report)
                    if fault=='same-context':r['reviewer_context']='producer'
                    elif fault=='owned-grade':r['grade']='owned-oracle'
                    elif fault=='missing-check':r['checks'].pop('wait')
                    elif fault=='missing-artifact':r['artifacts']=[]
                    elif fault=='wrong-output':r['artifacts'][0]['path']='source.md'
                    elif fault=='wrong-scope':r['scope']='other scope'
                    else:r['artifacts'][0]['sha256']='0'*64
                    (root/'review.json').write_text(json.dumps(r));graph['attestations']={'native':{'path':'review.json','sha256':sha(root/'review.json')}}
                    with self.assertRaises(ValueError):plan(root,graph,'evidence-verifier')
            (root/'review.json').write_text(json.dumps(report));graph['attestations']={'native':{'path':'review.json','sha256':sha(root/'review.json')}}
            result=plan(root,graph,'evidence-verifier');self.assertTrue(result['milestone1_complete']);self.assertFalse(result['milestone2_complete'])

    def handoff_fixture(self,root):
        (root/'behavior.md').write_text('A rejected edit retains the last accepted frame.')
        return {'verdict':'approved','author_context':'author','reviewer_context':'reviewer','behavior_only_reviewed':True,'provenance_reviewed':True,'files':[{'path':'behavior.md','name':'behavior.md','kind':'behavior-spec','sha256':sha(root/'behavior.md'),'public_provenance':'Owned black-box observation'}]}

    def test_handoff_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=self.handoff_fixture(root)
            for fault in ['same-context','unreviewed','changed','private-kind','escape','symlink','reserved','asset-license']:
                with self.subTest(fault=fault):
                    review=copy.deepcopy(base);row=review['files'][0]
                    if fault=='same-context':review['reviewer_context']='author'
                    elif fault=='unreviewed':review['behavior_only_reviewed']=False
                    elif fault=='changed':row['sha256']='0'*64
                    elif fault=='private-kind':row['kind']='decompilation'
                    elif fault=='escape':row['name']='../escape.md'
                    elif fault=='symlink':
                        link=root/'link.md'
                        if not link.exists():link.symlink_to(root/'behavior.md')
                        row['path']='link.md'
                    elif fault=='reserved':row['name']='HANDOFF-MANIFEST.json'
                    else:row['kind']='licensed-asset'
                    (root/'review.json').write_text(json.dumps(review));dest=root/'export'
                    with self.assertRaises(ValueError):export_handoff(root,'review.json',dest)
                    self.assertFalse(dest.exists())

    def test_handoff_exact_allowlist_no_internal_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);review=self.handoff_fixture(root);(root/'private-dump.txt').write_text('Do not export')
            (root/'review.json').write_text(json.dumps(review));dest=root/'bundle';result=export_handoff(root,'review.json',dest)
            self.assertEqual({p.name for p in dest.iterdir()},{'behavior.md','HANDOFF-MANIFEST.json'});self.assertFalse(result['runtime_isolation_enforced'])
            self.assertNotIn('"path"',(dest/'HANDOFF-MANIFEST.json').read_text())
            with self.assertRaises(ValueError):export_handoff(root,'review.json',dest)

    def test_legacy_execute_denied_without_creating_wake(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'research/loop';p.mkdir(parents=True);(p/'continuous.json').write_text(json.dumps({'clean_room_boundary':{'user_required':True}}))
            controller=SimpleNamespace(root=root,state=root,lock=nullcontext)
            with patch('reloop.graphloop.configuration',return_value=({},{})):
                with self.assertRaisesRegex(ValueError,'Clean-room boundary active'):run(controller)
            self.assertFalse((root/'graph-loop.json').exists())
