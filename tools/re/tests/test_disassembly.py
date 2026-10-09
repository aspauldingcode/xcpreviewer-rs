import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from reloop.disassembly import has_entry,normalize_words
from reloop.discriminants import instructions


class DisassemblyTests(unittest.TestCase):
    def test_heading_and_wrong_entry_do_not_certify_body(self):
        self.assertFalse(has_entry('0000000000030a00 <symbol>:\n',0x30a00))
        self.assertFalse(has_entry(' 30a04: fd 03 00 91 mov x29, sp',0x30a00))
        self.assertFalse(has_entry(' 30a00: symbol heading',0x30a00))
        self.assertTrue(has_entry(' 30a00: fd 7b bf a9 stp x29, x30, [sp, #-0x10]!',0x30a00))

    def test_word_normalization_preserves_instruction_bits(self):
        text=' 30a00: a9bf7bfd stp x29, x30, [sp, #-0x10]!\n 30a10: d65f03c0 ret\n'
        self.assertTrue(has_entry(text,0x30a00))
        normalized=normalize_words(text);code=instructions(normalized)
        self.assertEqual(code[0x30a00][2],0xa9bf7bfd)
        self.assertEqual(code[0x30a10][2],0xd65f03c0)
        self.assertEqual(code[0x30a10][:2],('ret',''))
        self.assertEqual(normalize_words(normalized),normalized)
