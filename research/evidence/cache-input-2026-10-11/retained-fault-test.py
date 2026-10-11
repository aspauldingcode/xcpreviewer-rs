import hashlib,importlib.util,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from reloop import sourcecache
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('cache_reader',Path(__file__).with_name('verify_cache_input.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CacheInputTests(unittest.TestCase):
 def test_sealed_failure_and_fix(self):
  e=ROOT/'research/evidence/cache-input-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['actual_producers'],4);self.assertEqual((ROOT/'tools/re/reloop/sourcecache.py').read_bytes(),(e/'fixed/sourcecache.py').read_bytes())
 def test_regular_limits_and_descriptor_release(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'owned';p.write_bytes(b'{}');fds=[];realopen=os.open
   def opened(*a,**k):fd=realopen(*a,**k);fds.append(fd);return fd
   with patch.object(sourcecache.os,'open',side_effect=opened):self.assertEqual(sourcecache.read_metadata(p,2),b'{}')
   for fd in fds:
    with self.assertRaises(OSError):os.fstat(fd)
   with self.assertRaises(ValueError):sourcecache.read_metadata(p,1)
   p.unlink();os.mkfifo(p)
   with self.assertRaises(ValueError):sourcecache.read_metadata(p,4096)
   p.unlink();p.symlink_to(Path(tmp)/'target');(Path(tmp)/'target').write_bytes(b'{}')
   with self.assertRaises(OSError):sourcecache.read_metadata(p,4096)
 def test_real_read_mutation_detected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'owned';p.write_bytes(b'{}');read=os.read
   def changed(*a,**k):p.write_bytes(b'{"changed":1}');return read(*a,**k)
   with patch.object(sourcecache.os,'read',side_effect=changed):
    with self.assertRaises(ValueError):sourcecache.read_metadata(p,4096)
 def test_resealed_faults(self):
  for fault in ['wait','timeout','reaped','calls','publication','module']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/cache-input-2026-10-11',e);root=e/'fixed/index';p=root/'wait.json';wait=json.loads(p.read_text());q=root/'after.json';after=json.loads(q.read_text())
    if fault=='wait':wait['code']=1
    elif fault=='timeout':wait['timeout']=True
    elif fault=='reaped':wait['reaped']=False
    elif fault=='calls':after['calls'].append(['extra compiler'])
    elif fault=='publication':after['pointer_hex']='00'
    else:after['module_hex']=('00'+after['module_hex'][2:])
    p.write_text(json.dumps(wait));q.write_text(json.dumps(after));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='2325301ad236cba6b2836e96fed0dd6a81e39e71ed6d6b4df3a5cf0b6422e223'
