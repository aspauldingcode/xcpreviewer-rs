import unittest
from reloop.resulttag import conditional, project


class ResultTagTests(unittest.TestCase):
    def test_zero_and_unequal_payload_sizes_preserve_every_other_byte(self):
        for a, b in [(0, 0), (0, 256), (256, 0), (24, 8), (8, 24), (17, 17)]:
            source = bytes(range(max(a, b) + 5)) if max(a, b) < 251 else bytes([0xa5]) * (max(a, b) + 5)
            for tag in (0, 1):
                result, offset, metadata = project(source, a, b, tag)
                self.assertEqual(offset, max(a, b))
                self.assertEqual(metadata, {0: 32, 1: 24}[tag])
                self.assertEqual(result[offset], tag)
                for i in range(len(source)):
                    if i != offset:
                        self.assertEqual(result[i], source[i])
                self.assertEqual(result[-4:], source[-4:])

    def test_result_has_no_state_trailer(self):
        result, offset, metadata = project(bytes([0xa5]) * 29, 24, 8, 1)
        self.assertEqual(offset, 24)
        self.assertEqual(result[24:], b'\x01' + b'\xa5' * 4)

    def test_domain_rejection(self):
        for a, b, tag in [(True, 8, 0), (-1, 8, 0), (0, 4097, 0), (0, 0, True), (0, 0, 2), (0, 0, -1)]:
            with self.assertRaises(ValueError):
                project(bytes(5000), a, b, tag)
        with self.assertRaises(ValueError):
            project(bytes(24), 24, 8, 0)

    def test_branch_target_condition_and_opcode_corruption(self):
        conditional(0x54000363, 0x2e884, 0x2e8f0, 3)
        for word, target, condition in [(0x54000362, 0x2e8f0, 3), (0x54000363, 0x2e8f4, 3), (0x14000363, 0x2e8f0, 3), (0x54000363, 0x2e8f0, 8)]:
            with self.assertRaises(ValueError):
                conditional(word, 0x2e884, target, condition)


if __name__ == '__main__':
    unittest.main()
