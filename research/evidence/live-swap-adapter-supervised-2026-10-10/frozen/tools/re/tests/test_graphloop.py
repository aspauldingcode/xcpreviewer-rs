import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from reloop.core import Controller, ROOT, atomic, canonical_hash, digest, evaluate, load
from reloop.graphloop import (configuration, frontier, independently_accepted,
                             inspect, overlay, run)
from reloop.loopverify import verify


class OwnedController(Controller):
    """Test execution writes real sealed evidence; no Apple/runtime action."""
    def __init__(self, root):
        super().__init__(root)
        self.executed = []
        self.fail = False
        self.crash = False

    def ready(self, queue, checkpoint, environment):
        return queue['experiments']

    def run_one(self, spec, environment, seconds_left=None, bytes_left=None):
        self.executed.append((spec['id'], seconds_left, bytes_left))
        rid = 'run-' + str(len(list(self.runs.iterdir())))
        folder = self.runs / rid
        folder.mkdir()
        atomic(folder / 'experiment.json', spec)
        result = {'observations': {'passed': not self.fail}}
        atomic(folder / 'output/result.json', result)
        verdict, checks = evaluate(spec['checks'], result)
        manifest = {'run_id': rid, 'experiment_id': spec['id'],
                    'experiment_hash': canonical_hash(spec), 'sealed': True,
                    'execution': 'success', 'verdict': verdict, 'checks': checks,
                    'tool_source_hashes': {}, 'artifacts': self.artifacts(folder)}
        atomic(folder / 'manifest.json', manifest)
        if self.crash:
            raise KeyboardInterrupt()
        return manifest


def experiment(eid):
    return {'id': eid, 'adapter': 'inventory', 'hypothesis': 'Owned control passes.',
            'depends_on': [], 'resources': ['local-re-controller'],
            'timeout_seconds': 10, 'artifact_limit_mb': 1, 'params': {},
            'priority': 50, 'checks': [{'path': 'passed', 'equals': True}]}


class GraphLoopTests(unittest.TestCase):
    def fixture(self, root, ids=('owned-one',)):
        controller = OwnedController(root)
        config = load(ROOT / 'research/loop/graph-runner.json')
        config['task_bindings'] = {'owned-task': list(ids)}
        atomic(root / 'research/loop/graph-runner.json', config)
        atomic(root / 'research/loop/campaign.json',
               {'version': 1, 'experiments': [experiment(eid) for eid in ids]})
        atomic(root / 'research/loop/workgraph.json',
               {'acceptance_attestations': {}, 'research_tasks': [
                   {'id': 'owned-task', 'issue': 'A', 'priority': 50, 'scope': 'owned test',
                    'requires_runs': [], 'completion_experiment_ids': list(ids)}]})
        atomic(root / 'research/loop/continuous.json', {'recent_evidence': [], 'blocked_tracks': []})
        atomic(root / 'research/roadmap/github.json', {'issues': {
            'A': {'milestone': 1, 'url': 'a', 'depends_on_ids': []},
            'B': {'milestone': 2, 'url': 'b', 'depends_on_ids': ['A']}}})
        (root / 'tools').mkdir()
        (root / 'tools/re').symlink_to(ROOT / 'tools/re', target_is_directory=True)
        return controller

    def test_two_experiments_required_before_task_complete_and_no_delivery_promotion(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={'target': 'owned'}):
            c = self.fixture(pathlib.Path(d), ('owned-one', 'owned-two'))
            wake = run(c)
            self.assertEqual([e[0] for e in c.executed], ['owned-one', 'owned-two'])
            self.assertEqual(len(wake['rounds']), 2)
            self.assertEqual(wake['state'], 'prerequisite-required')
            self.assertTrue(all(r['verification']['valid'] for r in wake['rounds']))
            view = inspect(c)
            self.assertEqual(view['candidates'], [])
            self.assertFalse(view['all_milestones_complete'])
            self.assertEqual(load(c.root / 'research/loop/workgraph.json')['acceptance_attestations'], {})

    def test_caveman_full_loaded_pinned_and_persisted(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d))
            wake = run(c)
            self.assertEqual(wake['communication']['intensity'], 'full')
            self.assertIn('ACTIVE EVERY RESPONSE', wake['communication']['instructions'])
            cfg = load(c.root / 'research/loop/graph-runner.json')
            cfg['communication']['sha256'] = '0' * 64
            atomic(c.root / 'research/loop/graph-runner.json', cfg)
            with self.assertRaisesRegex(ValueError, 'skill missing or changed'):
                configuration(c)

    def test_shared_round_and_byte_budgets_not_renewed_on_resume(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d), ('owned-one', 'owned-two'))
            path = c.root / 'research/loop/graph-runner.json'
            cfg = load(path); cfg['limits']['rounds'] = 1; atomic(path, cfg)
            wake = run(c)
            self.assertEqual(wake['state'], 'budget-exhausted')
            resumed = run(c, wake['id'])
            self.assertEqual(len(c.executed), 1)
            self.assertEqual(resumed['deadline'], wake['deadline'])
            self.assertGreater(resumed['artifact_bytes'], 0)
            self.assertEqual(c.executed[0][2], cfg['limits']['artifact_bytes'])

    def test_expired_budget_never_executes(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d))
            cfg, mode = configuration(c)
            wake = {'id': 'old', 'deadline': time.time() - 1, 'config_hash': canonical_hash(cfg),
                    'limits': cfg['limits'], 'rounds': [], 'state': 'running',
                    'artifact_bytes': 0, 'experiments': 0, 'communication': mode}
            atomic(c.state / 'graph-loop.json', {'accepted': {}, 'failures': {},
                                               'wakes': {'old': wake}, 'active_wake': 'old'})
            self.assertEqual(run(c)['state'], 'budget-exhausted')
            self.assertEqual(c.executed, [])

    def test_failure_requires_change_across_wakes(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d)); c.fail = True
            first = run(c)
            self.assertEqual(first['rounds'][0]['state'], 'failure-retained')
            second = run(c)
            self.assertEqual(len(c.executed), 1)
            self.assertEqual(second['candidates'][0]['state'], 'changed-prerequisite-required')
            with patch('reloop.graphloop.identity', return_value={'changed': True}):
                run(c)
            self.assertEqual(len(c.executed), 2)

    def test_interruption_reconciles_once_and_keeps_deadline(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d)); c.crash = True
            with self.assertRaises(KeyboardInterrupt): run(c)
            saved = load(c.state / 'graph-loop.json')
            deadline = saved['wakes'][saved['active_wake']]['deadline']
            c.crash = False
            resumed = run(c)
            self.assertEqual(resumed['deadline'], deadline)
            self.assertEqual(len(c.executed), 1)
            self.assertEqual(resumed['rounds'][0]['state'], 'failure-retained')
            self.assertGreater(resumed['artifact_bytes'], 0)

    def test_changed_spec_invalidates_local_completion(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d)); run(c)
            path = c.root / 'research/loop/campaign.json'
            queue = load(path); queue['experiments'][0]['hypothesis'] = 'Changed hypothesis.'; atomic(path, queue)
            self.assertEqual(inspect(c)['candidates'][0]['state'], 'ready')

    def test_corrupt_artifact_not_promoted(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d)); wake = run(c)
            rid = wake['rounds'][0]['run_id']
            (c.runs / rid / 'output/result.json').write_text('{}')
            cfg, _ = configuration(c)
            p, q = overlay(c, load(c.state / 'graph-loop.json'), cfg)
            self.assertNotIn('completion_runs', p['research_tasks'][0])
            self.assertEqual(q['recent_evidence'], [])

    def test_conflicting_external_anchor_and_quarantine_win(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d)); wake = run(c)
            rid = wake['rounds'][0]['run_id']
            path = c.root / 'research/loop/continuous.json'
            atomic(path, {'recent_evidence': [{'run_id': rid, 'manifest_sha256': '0' * 64}]})
            cfg, _ = configuration(c)
            p, _ = overlay(c, load(c.state / 'graph-loop.json'), cfg)
            self.assertNotIn('completion_runs', p['research_tasks'][0])
            atomic(path, {'recent_evidence': [], 'quarantined_evidence': [{'run_id': rid}]})
            p, _ = overlay(c, load(c.state / 'graph-loop.json'), cfg)
            self.assertNotIn('completion_runs', p['research_tasks'][0])

    def test_unknown_binding_and_scope_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.fixture(pathlib.Path(d)); cfg, _ = configuration(c)
            cfg['task_bindings']['missing'] = ['owned-one']
            with self.assertRaisesRegex(ValueError, 'Unknown graph task'):
                frontier(c, cfg, {}, {})
            cfg['task_bindings'] = {'owned-task': ['not-present']}
            with self.assertRaisesRegex(ValueError, 'Unknown bound experiment'):
                frontier(c, cfg, {}, {})

    def test_mechanical_verifier_rejects_wrong_checks_even_with_new_anchor(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.fixture(pathlib.Path(d))
            manifest = c.run_one(experiment('owned-one'), {})
            path = c.runs / manifest['run_id'] / 'manifest.json'
            manifest['checks'] = []; atomic(path, manifest)
            result = verify(c, manifest['run_id'], digest(path), manifest['experiment_hash'])
            self.assertFalse(result['valid'])

    def test_complete_requires_sealed_independent_review_for_each_delivery(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.fixture(pathlib.Path(d))
            graph = {'all_milestones_complete': True, 'nodes': [{'kind': 'delivery', 'id': 'A'}]}
            self.assertFalse(independently_accepted(c, graph))
            manifest = c.run_one(experiment('owned-one'), {})
            folder = c.runs / manifest['run_id']
            report = {'issue': 'A', 'independent': True, 'reviewer_id': 'separate-review-context',
                      'verdict': 'accepted', 'coverage_path': 'coverage.json', 'coverage': [{'id': 'required-control', 'accepted': True}]}
            atomic(folder / 'review.json', report)
            atomic(folder / 'coverage.json', {'required_checks': ['required-control']})
            manifest['artifacts'] = c.artifacts(folder); atomic(folder / 'manifest.json', manifest)
            p = load(c.root / 'research/loop/workgraph.json')
            p['acceptance_attestations']['A'] = {'runs': [manifest['run_id']], 'coverage_path': 'coverage.json',
                'independent_review': {'run_id': manifest['run_id'], 'path': 'review.json'}}
            atomic(c.root / 'research/loop/workgraph.json', p)
            atomic(c.root / 'research/loop/continuous.json', {'recent_evidence': [
                {'run_id': manifest['run_id'], 'manifest_sha256': digest(folder / 'manifest.json')}]})
            self.assertTrue(independently_accepted(c, graph))
            report['coverage'][0]['accepted'] = False; atomic(folder / 'review.json', report)
            self.assertFalse(independently_accepted(c, graph))

    def test_native_controller_lock_excludes_runner(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.fixture(pathlib.Path(d))
            with c.lock():
                with self.assertRaisesRegex(RuntimeError, 'another controller'):
                    run(c)
            self.assertEqual(c.executed, [])

    def test_resume_config_cannot_replenish_budget(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.graphloop.identity', return_value={}):
            c = self.fixture(pathlib.Path(d)); wake = run(c)
            path = c.root / 'research/loop/graph-runner.json'
            cfg = load(path); cfg['limits']['minutes'] = 14; atomic(path, cfg)
            with self.assertRaisesRegex(ValueError, 'configuration changed'):
                run(c, wake['id'])
