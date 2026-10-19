"""Synthetic fault controls only; never launches the C source."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import compare as c

class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        identity = c.expected_identity()
        # Deliberately synthetic contrasting producer bytes, never native evidence.
        nonlinear = bytearray(identity)
        nonlinear[48] ^= 1
        self.old = [bytes(nonlinear), identity]
        self.rows = []
        for route in range(2):
            source = c.expected_provider()
            (self.root / ('route%d-provider.raw' % route)).write_bytes(source)
            (self.root / ('route%d-readback.raw' % route)).write_bytes(identity)
            self.rows.append({'route': route, 'pid': 100, 'provider_bytes': c.PROVIDER_SIZE,
                'width': 768, 'height': 3, 'image_stride': 12352, 'image_bits_per_component': 32,
                'image_bits_per_pixel': 128, 'image_bitmap_info': 8449, 'stride': 12352,
                'allocation_bytes': 49152, 'bits_per_component': 32, 'bits_per_pixel': 128,
                'bitmap_info': 8449, 'color_space': 'kCGColorSpaceLinearSRGB',
                'source_color_space': 'kCGColorSpaceLinearSRGB' if route else 'kCGColorSpaceSRGB',
                'provider_file': 'route%d-provider.raw' % route, 'file': 'route%d-readback.raw' % route,
                'provider_sha256': c.digest(source), 'sha256': c.digest(identity)})

    def run_case(self):
        return c.compare(self.root, self.rows, self.old)

    def change(self, route, key, offset):
        p = self.root / self.rows[route][key]
        raw = bytearray(p.read_bytes()); raw[offset] ^= 1; p.write_bytes(raw)
        self.rows[route]['provider_sha256' if key == 'provider_file' else 'sha256'] = c.digest(raw)

    def test_independent_layout_and_branches(self):
        # Hand-written IEEE values independently check generator endpoints/channel placement.
        provider = c.expected_provider()
        self.assertEqual(provider[:48], b'\0' * 48)
        self.assertEqual(provider[765*16:765*16+16], bytes.fromhex('0000803f00000000000000000000803f'))
        self.assertEqual(provider[48:64], bytes.fromhex('8180803b00000000000000008180803b'))
        self.assertEqual(provider[384*16:384*16+16], bytes.fromhex('8180003f00000000000000008180003f'))
        self.assertEqual(provider[12288:12352], b'\xa5' * 64)
        result = self.run_case()
        self.assertEqual(result['all_bytes_compared'], 172416)
        self.assertTrue(result['linear_identity_control'])
        self.assertTrue(result['routes'][0]['identity']['exact'])
        self.assertFalse(result['routes'][0]['historical_8bit_relation']['exact'])
        self.assertFalse(result['native_acquisition_qualified'])
        self.assertFalse(result['canvas_qualified'])
        (self.root / self.rows[0]['file']).write_bytes(self.old[0])
        self.rows[0]['sha256'] = c.digest(self.old[0])
        other = self.run_case()
        self.assertFalse(other['routes'][0]['identity']['exact'])
        self.assertTrue(other['routes'][0]['historical_8bit_relation']['exact'])

    def test_rehashed_padding_tail_and_provider(self):
        for key, offset in [('provider_file', 12288), ('provider_file', 48), ('file', 12288), ('file', 37056), ('file', 49151)]:
            with self.subTest(key=key, offset=offset):
                p = self.root / self.rows[0][key]; original = p.read_bytes(); rows = copy.deepcopy(self.rows)
                self.change(0, key, offset)
                with self.assertRaises(ValueError): self.run_case()
                p.write_bytes(original); self.rows = rows

    def test_active_mismatch_is_retained(self):
        self.change(0, 'file', 48)
        result = self.run_case()
        self.assertEqual(result['routes'][0]['identity']['mismatch_bytes'], 1)
        self.assertFalse(result['native_acquisition_qualified'])
        self.change(1, 'file', 48)
        self.assertFalse(self.run_case()['linear_identity_control'])

    def test_typed_metadata_profiles_and_paths(self):
        faults = [('route', False), ('pid', True), ('pid', 0), ('image_stride', 12352.0),
                  ('image_bits_per_component', 8), ('source_color_space', 'kCGColorSpaceLinearSRGB'),
                  ('color_space', 'kCGColorSpaceSRGB'), ('file', '../elsewhere'), ('sha256', '0'*64)]
        for key, value in faults:
            with self.subTest(key=key):
                original = self.rows[0][key]; self.rows[0][key] = value
                with self.assertRaises(ValueError): self.run_case()
                self.rows[0][key] = original
        self.rows[1]['pid'] = 101
        with self.assertRaises(ValueError): self.run_case()

    def test_json_and_historical_contrast(self):
        for raw in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"unused":[{"nested":1e999}]}', '{"a":-1e999}']:
            with self.assertRaises(ValueError): c.parsed(raw)
        self.old[0] = self.old[1]
        with self.assertRaises(ValueError): self.run_case()

    def test_length_and_symlink(self):
        path = self.root / self.rows[0]['file']; raw = path.read_bytes()
        path.write_bytes(raw[:-1])
        with self.assertRaises(ValueError): self.run_case()
        path.unlink(); target = self.root / 'other.raw'; target.write_bytes(raw); path.symlink_to(target)
        with self.assertRaises(ValueError): self.run_case()

if __name__ == '__main__': unittest.main()
