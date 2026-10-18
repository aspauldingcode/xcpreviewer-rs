import unittest,tempfile,json,os
from pathlib import Path
from decoder import expected,canonical,filename,record,directory
I={'nonce':'60fd2da461f6404ea93e47eb59d6831a','pid':12345,'view':'01234567-89ab-cdef-0123-456789abcdef'}
class Tests(unittest.TestCase):
 def fixture(self,p,n=3):
  for i in range(n+1):
   v=expected(I,'appear' if i==0 else 'increment',i,i);(p/filename(v)).write_bytes(canonical(v))
 def test_literal_independent_bytes(self):
  literal=b'{"count":0,"event":"appear","nonce":"60fd2da461f6404ea93e47eb59d6831a","pid":12345,"schema":1,"sequence":0,"view":"01234567-89ab-cdef-0123-456789abcdef"}\n'
  self.assertEqual(record(literal,filename(expected(I,'appear',0,0)),I,'appear',0,0)['count'],0)
 def test_full_sequence(self):
  with tempfile.TemporaryDirectory() as d:
   self.fixture(Path(d));self.assertEqual([v['count'] for v in directory(d,I,3)],[0,1,2,3])
 def test_byte_mutants(self):
  v=expected(I,'appear',0,0);raw=canonical(v)
  for bad in [raw[:-1],raw+b' ',raw.replace(b'"count":0',b'"count":false'),raw.replace(b'"schema":1',b'"schema":2'),raw.replace(b'"count":0',b'"count":0,"count":0'),raw.replace(b'"event":"appear"',b'"event":"increment"'),json.dumps(v).encode()+b'\n',raw+b'\x00',b'X'*513]:
   with self.assertRaises(ValueError):record(bad,filename(v),I,'appear',0,0)
 def test_identity_filename_and_gap(self):
  v=expected(I,'appear',0,0)
  for bad in ['wrong.json',filename(v).replace('sequence-0','sequence-1')]:
   with self.assertRaises(ValueError):record(canonical(v),bad,I,'appear',0,0)
  for key,value in [('pid',True),('nonce','A'*32),('view','invalid')]:
   other={**I,key:value}
   with self.assertRaises(ValueError):expected(other,'appear',0,0)
 def test_missing_extra_and_pending(self):
  for mode in ['missing','extra','pending']:
   with tempfile.TemporaryDirectory() as d:
    p=Path(d);self.fixture(p)
    if mode=='missing':next(p.iterdir()).unlink()
    else:(p/('.pending-x' if mode=='pending' else 'extra.json')).write_bytes(b'{}')
    with self.assertRaises(ValueError):directory(p,I,3)
 def test_symlink_and_nonregular(self):
  with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
   p=Path(d);self.fixture(p);f=p/filename(expected(I,'appear',0,0));raw=f.read_bytes();f.unlink();target=Path(other)/'receipt';target.write_bytes(raw);f.symlink_to(target)
   with self.assertRaises(OSError):directory(p,I,3)
   f.unlink();os.mkfifo(f)
   with self.assertRaises(ValueError):directory(p,I,3)
   alias=Path(other)/'alias';alias.symlink_to(p,target_is_directory=True)
   with self.assertRaises(ValueError):directory(alias,I,3)
 def test_wrong_transcript_and_numeric_scope(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p);f=p/filename(expected(I,'increment',2,2));f.write_bytes(canonical(expected(I,'increment',2,1)))
   with self.assertRaises(ValueError):directory(p,I,3)
  for n in [True,-1,4]:
   with self.assertRaises(ValueError):directory('/private/tmp',I,n)
if __name__=='__main__':unittest.main()
