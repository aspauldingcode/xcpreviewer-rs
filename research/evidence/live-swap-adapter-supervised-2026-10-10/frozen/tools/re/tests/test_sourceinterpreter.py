import unittest
from reloop.sourceinterpreter import checker, expected_count


class SourceInterpreterTests(unittest.TestCase):
    def test_fault_counts_and_invalid_checker_calls(self):
        for function in ('verify', 'verify_rejected'):
            for argument in range(5):
                self.assertEqual(expected_count(function, argument), 0xffffffff if argument == 4 else (1 if function == 'verify' and argument else 0))
        for function, argument in [('render', 0), ('verify', True), ('verify', -1), ('verify_rejected', '1')]:
            with self.assertRaises(ValueError):expected_count(function, argument)

    def test_geometry_rejects_outside_memory_and_source_contract(self):
        for args in [(0, 16, 3), (33, 16, 3), (32, 11, 3), (32, 1281, 3), (32, 16, 0), (32, 16, 321), (204801, 1280, 320), (2576, 16, 3), (True, 16, 3)]:
            with self.assertRaises(ValueError):checker(*args)


if __name__ == '__main__':unittest.main()
