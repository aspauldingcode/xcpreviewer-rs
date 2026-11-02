import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1] / "swiftui-preview"
sys.path.insert(0, str(HERE))
import watch
import capture
import discover

class WatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "Original.swift"
        self.source.write_bytes(b"first")
        self.output = self.root / "frame.bplist"
        self.png = self.root / "frame.png"
        self.output.write_bytes(b"last-good")
        self.png.write_bytes(b"last-good-png")
        self.args = SimpleNamespace(source=str(self.source), output=str(self.output),
            reference_png=str(self.png), once=True, interval=0.05, debounce=0)

    def producer(self, local):
        self.assertEqual(Path(local.source).read_bytes(), b"first")
        self.assertNotEqual(Path(local.output), self.output)
        Path(local.output).write_bytes(b"new-frame")
        Path(local.reference_png).write_bytes(b"new-png")
        return {"output": local.output}

    def test_stable_snapshot_publishes_both_outputs_and_real_path(self):
        result = watch.attempt(self.args, self.source, b"first", self.producer)
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["capture"]["source"], str(self.source))
        self.assertEqual(self.output.read_bytes(), b"new-frame")
        self.assertEqual(self.png.read_bytes(), b"new-png")

    def test_edit_during_capture_discards_both_scratch_outputs(self):
        def changed(local):
            result = self.producer(local)
            self.source.write_bytes(b"second")
            return result
        result = watch.attempt(self.args, self.source, b"first", changed)
        self.assertEqual(result["status"], "superseded")
        self.assertEqual(self.output.read_bytes(), b"last-good")
        self.assertEqual(self.png.read_bytes(), b"last-good-png")

    def test_failure_or_deleted_source_preserves_last_good(self):
        for deleted in [False, True]:
            self.source.write_bytes(b"first")
            def failed(local):
                self.producer(local)
                if deleted:
                    self.source.unlink()
                    return {}
                raise RuntimeError("owned producer failed")
            with self.assertRaises((RuntimeError, FileNotFoundError)):
                watch.attempt(self.args, self.source, b"first", failed)
            self.assertEqual(self.output.read_bytes(), b"last-good")
            self.assertEqual(self.png.read_bytes(), b"last-good-png")

    def test_alias_source_and_symlink_rejected_before_producer(self):
        for destination in [self.source, self.root / "alias"]:
            if destination != self.source:
                destination.symlink_to(self.output)
            self.args.output = str(destination)
            with self.assertRaises(ValueError):
                watch.attempt(self.args, self.source, b"first", self.producer)
        self.assertEqual(self.source.read_bytes(), b"first")

    def test_failed_revision_not_retried_until_content_changes(self):
        self.args.once = False
        emitted = []
        sleeps = 0
        def sleep(_):
            nonlocal sleeps
            sleeps += 1
            if sleeps == 2:
                self.source.write_bytes(b"changed")
            if sleeps == 4:
                raise KeyboardInterrupt()
        with patch.object(watch, "attempt", side_effect=RuntimeError("failure")) as attempt, patch.object(watch.time, "sleep", side_effect=sleep):
            with self.assertRaises(KeyboardInterrupt):
                watch.watch(self.args, emitted.append)
        self.assertEqual(attempt.call_count, 2)
        self.assertEqual([x["status"] for x in emitted], ["capturing", "capture-error"]*2)

    def test_interrupt_reaps_only_created_process_group(self):
        for module in [capture, discover]:
            process = unittest.mock.Mock(pid=54321, returncode=-9)
            process.communicate.side_effect = [KeyboardInterrupt(), (b"", b"")]
            with patch.object(module.subprocess, "Popen", return_value=process) as start, patch.object(module.os, "killpg") as kill:
                with self.assertRaises(KeyboardInterrupt):
                    module.run(["owned-helper"], 1, {})
                self.assertTrue(start.call_args.kwargs["start_new_session"])
                kill.assert_called_once_with(54321, module.signal.SIGKILL)
                self.assertEqual(process.communicate.call_count, 2)

if __name__ == "__main__":
    unittest.main()
