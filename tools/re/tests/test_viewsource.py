import unittest
from reloop.viewsource import HOLDOUTS, lower, parse, stable_ir
from reloop.core import validate_experiment


class ViewSourceTests(unittest.TestCase):
    def test_supported_expression_and_ascii_whitespace(self):
        self.assertEqual(parse('Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 320, height: 160)'), {'color': 'red', 'width': 320, 'height': 160})
        self.assertEqual(parse(' \nColor ( .sRGB , red : 0 , green : 0 , blue : 1 , opacity : 1 ) .frame ( width : 3 , height : 2 )\t'), {'color': 'blue', 'width': 3, 'height': 2})

    def test_every_holdout_rejects(self):
        for source in HOLDOUTS:
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse(source)

    def test_bounded_input_and_size_domain(self):
        for source in [None, b'Color.red', ' ' * 4097, 'Color.red.frame(width: 1, height: 0)', 'Color.red.frame(width: 1000, height: 2)']:
            with self.assertRaises(ValueError):parse(source)
        self.assertEqual(parse('Color(.sRGB, red: 0, green: 0, blue: 1, opacity: 1).frame(width: 1, height: 1)')['width'], 1)

    def test_codegen_revalidates_instead_of_interpolating_code(self):
        for config in [{'color': 'red;system(0)', 'width': 1, 'height': 1}, {'color': 'red', 'width': True, 'height': 1}, {'color': 'blue', 'width': '320', 'height': 160}, {'color': 'red', 'width': 321, 'height': 1}, {'color': 'red', 'width': 1, 'height': 1, 'extra': 1}]:
            with self.assertRaises(ValueError):lower(config)
        text = lower({'color': 'blue', 'width': 3, 'height': 2})
        self.assertIn('stride < 12', text)
        self.assertIn('buffer[i] = 0', text)
        self.assertIn('buffer[i+2] = 255', text)

    def test_source_flag_and_runtime_contract_validation(self):
        e = {'id': 'source-control', 'adapter': 'portable_solid', 'hypothesis': 'Bounded source', 'params': {'source_control': True}, 'priority': 90, 'timeout_seconds': 120, 'artifact_limit_mb': 16, 'depends_on': [], 'resources': [], 'checks': [{'path': 'valid', 'equals': True}]}
        validate_experiment(e)
        for value in [1, 'true', None]:
            e['params'] = {'source_control': value}
            with self.assertRaises(ValueError):validate_experiment(e)
        e['params'] = {'source_control': True, 'second_runtime': True}
        validate_experiment(e)

    def test_ir_normalization_preserves_all_nonheader_bytes(self):
        tail = 'target triple = "wasm32"\n\ndefine i32 @render() { ret i32 0 }\n'
        a = '; ModuleID = \'/a/source-0.c\'\nsource_filename = "/a/source-0.c"\n' + tail
        b = '; ModuleID = \'/b/source-1.c\'\nsource_filename = "/b/source-1.c"\n' + tail
        self.assertEqual(stable_ir(a), stable_ir(b))
        self.assertEqual(''.join(stable_ir(a).splitlines(keepends=True)[2:]), tail)
        for bad in ['', 'define i32 @render() { ret i32 0 }', '; ModuleID = a\nnot source metadata\n' + tail]:
            with self.assertRaises(ValueError):stable_ir(bad)


if __name__ == '__main__':
    unittest.main()
