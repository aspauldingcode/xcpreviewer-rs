"""Canonical adapter boundary and its graph binding are explicitly constrained."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from reloop.core import ROOT, validate_experiment
from reloop.worker import perform


class LiveSwapBindingTests(unittest.TestCase):
    def test_fixed_adapter_rejects_parameter_expansion(self):
        queue = json.loads((ROOT / 'research/loop/campaign.json').read_text())
        spec = next(e for e in queue['experiments'] if e['id'] == 'primary-live-wasm-swap')
        validate_experiment(spec)
        mutant = copy.deepcopy(spec)
        mutant['params'] = {'arbitrary_script': '/tmp/unreviewed.js'}
        with self.assertRaises(ValueError):
            validate_experiment(mutant)
        binding = json.loads((ROOT / 'research/loop/live-swap-runner.json').read_text())
        self.assertEqual(binding['task_bindings'], {spec['id']: [spec['id']]})
        self.assertEqual(binding['limits']['experiments'], 1)

    def test_dispatch_uses_consolidated_adapter(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('reloop.liveswapprobe.corpus', return_value={'frames': 84}) as adapter:
                self.assertEqual(perform('live_swap', Path(folder), {}), {'frames': 84})
                adapter.assert_called_once_with(Path(folder))
