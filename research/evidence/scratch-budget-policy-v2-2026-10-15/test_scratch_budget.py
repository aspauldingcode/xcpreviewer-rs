import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scratch_budget import CAS, GIB, admit, measure, new_root


class AccountingTests(unittest.TestCase):
    def test_fresh_private_root_and_identity(self):
        with tempfile.TemporaryDirectory() as parent:
            root, identity = new_root(parent)
            self.assertTrue(admit(measure(root, identity=identity)))
            with self.assertRaises(ValueError):
                measure(root, identity=(identity[0], identity[1] + 1))
            root.chmod(0o755)
            with self.assertRaises(ValueError):
                measure(root, identity=identity)

    def test_early_entry_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for number in range(5):
                (root / str(number)).write_bytes(b'x')
            with self.assertRaises(ValueError):
                measure(root, max_entries=2)

    def test_traversal_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('scratch_budget.time.monotonic', return_value=10):
                with self.assertRaises(TimeoutError):
                    measure(directory, deadline=9)
    def test_three_declared_sparse_extents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, size in CAS.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('wb') as stream:
                    stream.truncate(size)
            actual = measure(root)
            self.assertEqual(actual['scratch_logical'], 25 * GIB)
            self.assertEqual(actual['retained_logical'], 0)
            self.assertTrue(admit(actual))

    def test_unlisted_sparse_output_still_counts_logical(self):
        with tempfile.TemporaryDirectory() as directory:
            with (Path(directory) / 'output.bin').open('wb') as stream:
                stream.truncate(GIB)
            actual = measure(directory)
            self.assertEqual(actual['retained_logical'], GIB)
            self.assertFalse(admit(actual))

    def test_oversized_named_extent_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            name, maximum = next(iter(CAS.items()))
            path = Path(directory) / name
            path.parent.mkdir(parents=True)
            with path.open('wb') as stream:
                stream.truncate(maximum + 1)
            with self.assertRaises(ValueError):
                measure(directory)

    def test_symlink_and_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'file').write_bytes(b'x')
            (root / 'link').symlink_to(root / 'file')
            with self.assertRaises(ValueError):
                measure(root)
            (root / 'link').unlink()
            os.link(root / 'file', root / 'hard')
            with self.assertRaises(ValueError):
                measure(root)

    def test_caps_fail_independently(self):
        valid = dict(retained_logical=0, scratch_logical=0, allocated=0, files=0, directories=0)
        self.assertTrue(admit(valid))
        for key, over in [('retained_logical', 512 * 1024 ** 2 + 1),
                          ('allocated', 512 * 1024 ** 2 + 1),
                          ('scratch_logical', 25 * GIB + 1), ('files', 100001)]:
            self.assertFalse(admit({**valid, key: over}))

    def test_unreadable_subtree_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('scratch_budget.os.scandir', side_effect=PermissionError('hidden subtree')):
                with self.assertRaises(PermissionError):
                    measure(directory)

    def test_partial_cas_shape_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / next(iter(CAS))
            path.parent.mkdir(parents=True)
            with path.open('wb') as stream:
                stream.truncate(GIB)
            result = measure(directory)
            self.assertEqual(result['scratch_logical'], 0)
            self.assertEqual(result['retained_logical'], GIB)
            self.assertFalse(admit(result))

    def test_directory_link_and_fifo_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'dir').mkdir()
            (root / 'link').symlink_to(root / 'dir', target_is_directory=True)
            with self.assertRaises(ValueError):
                measure(root)
            (root / 'link').unlink()
            os.mkfifo(root / 'pipe')
            with self.assertRaises(ValueError):
                measure(root)

    def test_exact_boundaries_and_negative_values(self):
        values = dict(retained_logical=512 * 1024 ** 2, scratch_logical=25 * GIB,
                      allocated=512 * 1024 ** 2, files=50000, directories=50000)
        self.assertTrue(admit(values))
        self.assertFalse(admit({**values, 'directories': 50001}))
        self.assertFalse(admit({**values, 'files': -1}))
        self.assertFalse(admit({**values, 'allocated': True}))


if __name__ == '__main__':
    unittest.main()
