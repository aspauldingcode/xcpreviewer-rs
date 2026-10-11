import io
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from reloop.core import atomic, load
from reloop.primarysource import expression, expected, parse
from reloop.sourceframe import png, render, straight_rgba, verify_bundle


class SourceFrameTests(unittest.TestCase):
    def test_artifact_scan_tolerates_directory_rename_but_not_access_failure(self):
        import os
        from reloop.core import tree_size
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);child=root/'staging';child.mkdir()
            (root/'kept').write_bytes(b'1234567');(child/'payload').write_bytes(b'bytes')
            scan=os.scandir
            def vanished(path):
                if pathlib.Path(path)==child:raise FileNotFoundError('Owned stage renamed')
                return scan(path)
            with patch('reloop.core.os.scandir',side_effect=vanished):
                self.assertEqual(tree_size(root),7)
            def denied(path):
                if pathlib.Path(path)==child:raise PermissionError('Access denied')
                return scan(path)
            with patch('reloop.core.os.scandir',side_effect=denied):
                with self.assertRaises(PermissionError):tree_size(root)

    def fixture(self, root):
        root = pathlib.Path(root)
        node = root / 'node'; node.write_bytes(b'owned node')
        return root / 'cache', root / 'preview', root / 'clang', root / 'ld', node

    def compiler(self, source, cache, output, clang, ld):
        folder = output / 'versions' / 'owned'; folder.mkdir(parents=True)
        for name in ('view.c', 'view.ll', 'view.wasm'):
            (folder / name).write_bytes(b'owned ' + name.encode())
        import hashlib
        return {'entry_sha256': 'owned', 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                'module_sha256': hashlib.sha256((folder / 'view.wasm').read_bytes()).hexdigest(),
                'cache_hit': False}

    def runtime(self, args, **kwargs):
        folder = pathlib.Path(args[4]); width, height, stride = map(int, args[5:])
        config = parse((folder / 'source.swift').read_text())
        (folder / 'allocation.raw').write_bytes(expected(config, stride))
        atomic(folder / 'runtime.json', {'node': 'owned', 'v8': 'owned', 'imports': 0,
               'memory_bytes': 131072, 'allocation_bytes': 16384,
               'rendered_bytes': stride * height, 'invalid_requests': 4, 'invalid_unchanged': True})
        return subprocess.CompletedProcess(args, 0)

    def test_png_alpha_conversion_independent_literal_pixels(self):
        cases = [([0, 0, 0], (0, 0, 0, 0)), ([0, 4, 0], (0, 255, 0, 128)),
                 ([4, 0, 4], (170, 0, 85, 192)), ([8, 0, 0], (255, 0, 0, 255))]
        for alphas, literal in cases:
            config = {'width': 2, 'height': 3, 'reverse': 0, 'alphas': alphas}
            rgba = straight_rgba(expected(config, 12), config, 12)
            self.assertEqual(rgba, bytes(literal) * 6)
            image = Image.open(io.BytesIO(png(rgba, 2, 3)))
            self.assertEqual(image.size, (2, 3))
            self.assertEqual(image.mode, 'RGBA')
            self.assertEqual(image.tobytes(), bytes(literal) * 6)
            self.assertEqual(image.info.get('srgb'), 0)

    def test_full_allocation_padding_tail_and_truncation_reject(self):
        config = parse(expression(4)); stride = 80; raw = expected(config, stride)
        for index in (0, 3, 68, 719, 720, 16383):
            damaged = bytearray(raw); damaged[index] ^= 1
            with self.assertRaises(ValueError): straight_rgba(bytes(damaged), config, stride)
        for wrong in (raw[:-1], raw + b'\0'):
            with self.assertRaises(ValueError): straight_rgba(wrong, config, stride)

    def test_transaction_preserves_last_good_after_failure(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.sourceframe.build', side_effect=self.compiler), patch('reloop.sourceframe.subprocess.run', side_effect=self.runtime):
            cache, output, clang, ld, node = self.fixture(d)
            receipt = render(expression(4), cache, output, clang, ld, node, stride=80)
            old = (output / 'current.json').read_bytes()
            with self.assertRaisesRegex(RuntimeError, 'pre-publication'):
                render(expression(8), cache, output, clang, ld, node, fault_before_commit=True)
            self.assertEqual((output / 'current.json').read_bytes(), old)
            for source in ('Text("bad")', expression(4)):
                with patch('reloop.sourceframe.subprocess.run', side_effect=subprocess.TimeoutExpired(['node'], 5)):
                    with self.assertRaises((ValueError, subprocess.TimeoutExpired)):
                        render(source, cache, output, clang, ld, node)
                self.assertEqual((output / 'current.json').read_bytes(), old)
            self.assertEqual(load(output / 'current.json')['entry_sha256'], receipt['entry_sha256'])
            self.assertEqual(list(output.glob('.owned-frame-*')), [])

    def test_runtime_failure_wrong_extent_missing_metadata_and_corruption(self):
        with tempfile.TemporaryDirectory() as d, patch('reloop.sourceframe.build', side_effect=self.compiler):
            cache, output, clang, ld, node = self.fixture(d)
            with patch('reloop.sourceframe.subprocess.run', side_effect=self.runtime):
                render(expression(4), cache, output, clang, ld, node)
            old = (output / 'current.json').read_bytes()
            def bad(args, **kwargs):
                result = self.runtime(args, **kwargs)
                folder = pathlib.Path(args[4])
                (folder / 'allocation.raw').write_bytes(bytes(16384))
                return result
            def metadata(args, **kwargs):
                result = self.runtime(args, **kwargs)
                atomic(pathlib.Path(args[4]) / 'runtime.json', {'imports': 0})
                return result
            for effect in (bad, metadata, lambda args, **kwargs: subprocess.CompletedProcess(args, 1)):
                with patch('reloop.sourceframe.subprocess.run', side_effect=effect):
                    with self.assertRaises((RuntimeError, ValueError)):
                        render(expression(4), cache, output, clang, ld, node)
                self.assertEqual((output / 'current.json').read_bytes(), old)
                self.assertEqual(list(output.glob('.owned-frame-*')), [])

    def test_bundle_tamper_lock_and_symlink_rejected(self):
        from reloop.sourcecache import lock
        with tempfile.TemporaryDirectory() as d, patch('reloop.sourceframe.build', side_effect=self.compiler), patch('reloop.sourceframe.subprocess.run', side_effect=self.runtime):
            cache, output, clang, ld, node = self.fixture(d)
            receipt = render(expression(4), cache, output, clang, ld, node)
            folder = output / 'versions' / receipt['entry_sha256']
            (folder / 'allocation.raw').write_bytes(b'bad')
            with self.assertRaises(ValueError): verify_bundle(folder, receipt['entry_sha256'])
            with lock(output, '.frame.lock'):
                with self.assertRaises(RuntimeError): render(expression(4), cache, output, clang, ld, node)
            pointer = output / 'current.json'; pointer.unlink()
            other = pathlib.Path(d) / 'other'; other.write_bytes(b'preserve'); pointer.symlink_to(other)
            with self.assertRaises(ValueError): render(expression(8), cache, output, clang, ld, node)
            self.assertEqual(other.read_bytes(), b'preserve')

    def test_deadlines_dimensions_and_invalid_stride_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            args = self.fixture(d)
            for timeout in (0, 11, float('nan'), float('inf'), True):
                with self.assertRaises(ValueError): render(expression(4), *args, timeout=timeout)
            for stride in (0, 67, 257, True):
                with self.assertRaises(ValueError): render(expression(4), *args, stride=stride)
        with self.assertRaises(ValueError): png(b'', 0, 1)
        with self.assertRaises(ValueError): png(b'', 1, 1)
