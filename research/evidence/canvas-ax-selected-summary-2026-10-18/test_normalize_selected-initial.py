import unittest
from normalize_selected import normalize
from path_binding import assess
from test_exposure import b,base,end
note='\n\nNote: Pay special attention to the content selected by the user. Remaining guidance.'
tree=base+'\t\t30 row (selected)\n'+end
selected=tree+'\nSelected:\n\t30 row (selected)'+note
class Tests(unittest.TestCase):
 def test_valid_summary(self):self.assertEqual(normalize(selected),tree.rstrip('\n'))
 def test_raw_reject_normalized_bind(self):
  with self.assertRaises(ValueError):assess(selected,b)
  self.assertEqual(assess(normalize(selected),b)['close_index'],9)
 def test_unknown_selected_index(self):
  with self.assertRaises(ValueError):normalize(selected.replace('\n\t30 row (selected)'+note,'\n\t31 row (selected)'+note))
 def test_changed_label(self):
  with self.assertRaises(ValueError):normalize(selected.replace('\n\t30 row (selected)'+note,'\n\t30 row (selected) other'+note))
 def test_actual_tree_duplicate(self):
  with self.assertRaises(ValueError):normalize(selected.replace('\t9 close button','\t\t30 row (selected)\n\t9 close button'))
 def test_injected_window(self):
  with self.assertRaises(ValueError):normalize(selected.replace('\t30 row (selected)'+note,'0 standard window other'+note))
 def test_missing_footer(self):
  with self.assertRaises(ValueError):normalize(selected.replace(note,''))
 def test_no_summary_unchanged(self):self.assertEqual(normalize(tree),tree)
if __name__=='__main__':unittest.main()
