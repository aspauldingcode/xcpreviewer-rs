import copy,json,pathlib,tempfile,unittest
from unittest.mock import patch
from reloop.core import atomic,canonical_hash,digest,load
from reloop.graphloop import adopt_verified,configuration,inspect
import test_graphloop as graph_tests

class GraphAdoptionTests(unittest.TestCase):
 def fixture(self,root):
  c=graph_tests.GraphLoopTests().fixture(root);spec=load(root/'research/loop/campaign.json')['experiments'][0]
  m=c.run_one(spec,{},1,1000000);return c,m,digest(c.runs/m['run_id']/'manifest.json')
 def test_fresh_adoption_is_idempotent_and_research_only(self):
  with tempfile.TemporaryDirectory() as tmp,patch('reloop.graphloop.identity',return_value={'target':'owned'}):
   c,m,anchor=self.fixture(pathlib.Path(tmp));first=adopt_verified(c,'owned-task',m['run_id'],anchor);second=adopt_verified(c,'owned-task',m['run_id'],anchor)
   self.assertTrue(first['verification']['valid']);self.assertEqual(first['scope'],'research-only');self.assertEqual(second['delivery_review'],'review-pending')
   self.assertEqual(len(load(c.state/'graph-loop.json')['accepted']['owned-task']),1);self.assertEqual(len(c.executed),1)
   view=inspect(c);self.assertFalse(view['all_milestones_complete']);self.assertEqual(view['candidates'],[])
 def test_missing_or_conflicting_evidence_rejected(self):
  for fault in ['anchor','hash','verdict','active','quarantine','conflict','scope','artifact']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    c,m,anchor=self.fixture(pathlib.Path(tmp));folder=c.runs/m['run_id']
    if fault=='anchor':anchor='0'*64
    elif fault in ['hash','verdict']:
     d=copy.deepcopy(m);d['experiment_hash' if fault=='hash' else 'verdict']='wrong';atomic(folder/'manifest.json',d);anchor=digest(folder/'manifest.json')
    elif fault=='active':atomic(c.state/'graph-loop.json',{'wakes':{'owned':{'state':'running'}}})
    elif fault in ['quarantine','conflict']:
     d=load(c.root/'research/loop/continuous.json');d['quarantined_evidence' if fault=='quarantine' else 'recent_evidence']=[{'run_id':m['run_id'],'manifest_sha256':'0'*64}];atomic(c.root/'research/loop/continuous.json',d)
    elif fault=='scope':
     d=load(c.root/'research/loop/workgraph.json');d['research_tasks'][0]['completion_experiment_ids']=['different'];atomic(c.root/'research/loop/workgraph.json',d)
    else:(folder/'output/result.json').write_text('{"observations":{"passed":false}}')
    with self.assertRaises(ValueError):adopt_verified(c,'owned-task',m['run_id'],anchor)
    self.assertFalse(load(c.state/'graph-loop.json',{}).get('accepted',{}))
 def test_default_reviewed_binding_preserves_limits_and_explicit_disable(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);c,_,_=self.fixture(root);live='primary-live-wasm-swap';original=load(root/'research/loop/graph-runner.json')
   atomic(root/'research/loop/live-swap-runner.json',{'schema_version':1,'task_bindings':{live:[live]}})
   policy=load(root/'research/loop/workgraph.json');policy['research_tasks'].append({'id':live});atomic(root/'research/loop/workgraph.json',policy)
   q=load(root/'research/loop/campaign.json');q['experiments'].append({'id':live,'adapter':'live_swap'});atomic(root/'research/loop/campaign.json',q)
   config,_=configuration(c);self.assertEqual(config['task_bindings'][live],[live]);self.assertEqual(config['limits'],original['limits']);self.assertEqual(load(root/'research/loop/graph-runner.json'),original)
   original['task_bindings'][live]=[];atomic(root/'research/loop/graph-runner.json',original);config,_=configuration(c);self.assertEqual(config['task_bindings'][live],[])
