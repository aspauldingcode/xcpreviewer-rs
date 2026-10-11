import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from reloop.linuxwasm import cleanup_owned, corpus


class LinuxWasmTests(unittest.TestCase):
    def test_unowned_container_is_never_removed(self):
        with tempfile.TemporaryDirectory() as directory, patch('reloop.linuxwasm.subprocess.run', return_value=subprocess.CompletedProcess([], 0, 'another-owner\n', '')) as run:
            with self.assertRaises(ValueError):cleanup_owned('owned-name', 'my-owner', pathlib.Path(directory))
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][1], 'inspect')

    def test_already_removed_container_does_not_require_force_removal(self):
        responses = [subprocess.CompletedProcess([], 1, '', 'not found'), subprocess.CompletedProcess([], 0, '', '')]
        with tempfile.TemporaryDirectory() as directory, patch('reloop.linuxwasm.subprocess.run', side_effect=responses) as run:
            cleanup_owned('owned-name', 'my-owner', pathlib.Path(directory))
            self.assertEqual([c.args[0][1] for c in run.call_args_list], ['inspect', 'ps'])

    def test_owned_container_removed_and_remaining_container_rejected(self):
        for remaining in ['', 'owned-name\n']:
            responses = [subprocess.CompletedProcess([], 0, 'my-owner\n', ''), subprocess.CompletedProcess([], 0, '', ''), subprocess.CompletedProcess([], 0, remaining, '')]
            with tempfile.TemporaryDirectory() as directory, patch('reloop.linuxwasm.subprocess.run', side_effect=responses) as run:
                if remaining:
                    with self.assertRaises(ValueError):cleanup_owned('owned-name', 'my-owner', pathlib.Path(directory))
                else:cleanup_owned('owned-name', 'my-owner', pathlib.Path(directory))
                self.assertEqual(run.call_args_list[1].args[0], ['docker', 'rm', '-f', 'owned-name'])

    def test_changed_source_anchor_or_runtime_wheel_blocks_execution(self):
        for anchor_valid, wheel in [(False, 'unused'), (True, 'bad-hash')]:
            with tempfile.TemporaryDirectory() as directory, patch('reloop.linuxwasm.Controller') as controller, patch('reloop.linuxwasm.digest', return_value=wheel), patch('reloop.linuxwasm.subprocess.run') as run:
                controller.return_value.verify.return_value = {'valid': anchor_valid}
                with self.assertRaises(ValueError):corpus(pathlib.Path(directory))
                run.assert_not_called()


if __name__ == '__main__':unittest.main()
