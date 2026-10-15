from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scratch_budget import measure


class LiveDisappearanceTests(unittest.TestCase):
    def exercise(self, relative, live, error=FileNotFoundError, count=1):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for number in range(count):
                path = root / relative.replace('MODULE', 'Module' + str(number))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'x')
                paths.append(path)
            real = Path.lstat
            def observed(path):
                if path in paths:
                    raise error(str(path))
                return real(path)
            with patch.object(Path, 'lstat', observed):
                return measure(root, live=live)

    def test_live_allowlisted_file_and_entry_count(self):
        value = self.exercise('DerivedData/ModuleCache.noindex/BN9Y5VQ6XBK3/MODULE-HASH-abc.pcm.tmp', True)
        self.assertEqual(value['vanished_count'], 1)
        self.assertEqual(value['files'], 1)

    def test_strict_final_rejects_same_file(self):
        with self.assertRaises(FileNotFoundError):
            self.exercise('DerivedData/ModuleCache.noindex/BN9Y5VQ6XBK3/MODULE-HASH-abc.pcm.tmp', False)

    def test_disallowed_path_and_permission_fail(self):
        with self.assertRaises(FileNotFoundError):
            self.exercise('output.bin', True)
        with self.assertRaises(PermissionError):
            self.exercise('DerivedData/ModuleCache.noindex/BN9Y5VQ6XBK3/MODULE-HASH-abc.pcm.tmp', True, PermissionError)

    def test_disappearance_limit_and_bounded_diagnostics(self):
        relative = 'DerivedData/ModuleCache.noindex/BN9Y5VQ6XBK3/MODULE-HASH-abc.pcm.tmp'
        value = self.exercise(relative, True, count=32)
        self.assertEqual(value['vanished_count'], 32)
        self.assertEqual(len(value['vanished_paths']), 16)
        with self.assertRaises(ValueError):
            self.exercise(relative, True, count=33)

    def test_root_and_directory_missing_remain_fatal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / 'dir'
            child.mkdir()
            real = Path.lstat
            for missing in [root, child]:
                def observed(path):
                    if path == missing:
                        raise FileNotFoundError(str(path))
                    return real(path)
                with patch.object(Path, 'lstat', observed):
                    with self.assertRaises(FileNotFoundError):
                        measure(root, live=True)


if __name__ == '__main__':
    unittest.main()
