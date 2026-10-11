import hashlib,importlib.util,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('input_reader',Path(__file__).with_name('verify_source_cli_input.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
s=importlib.util.spec_from_file_location('source_cli',ROOT/'tools/re/source_cli.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
class SourceCliInputTests(unittest.TestCase):
 def test_sealed_process_outcomes(self):
  e=ROOT/'research/evidence/source-cli-input-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['actual_cli_processes'],4);self.assertEqual((ROOT/'tools/re/source_cli.py').read_bytes(),(e/'fixed/source_cli.py').read_bytes())
 def test_regular_rejections_and_descriptor_release(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'source';p.write_bytes(b'owned ascii');fds=[];realopen=os.open
   def opened(*args,**kwargs):fd=realopen(*args,**kwargs);fds.append(fd);return fd
   with patch.object(cli.os,'open',side_effect=opened):self.assertEqual(cli.read_source(p),'owned ascii')
   for fd in fds:
    with self.assertRaises(OSError):os.fstat(fd)
   for raw in [b'x'*4097,b'\xff']:
    p.write_bytes(raw)
    with self.assertRaises((ValueError,UnicodeError)):cli.read_source(p)
   p.unlink();os.mkfifo(p)
   with self.assertRaises(ValueError):cli.read_source(p)
   p.unlink();p.symlink_to(Path(tmp)/'target');(Path(tmp)/'target').write_bytes(b'valid')
   with self.assertRaises(OSError):cli.read_source(p)
   with self.assertRaises(ValueError):cli.read_source(Path(tmp))
 def test_owned_replacement_and_mutation_reject(self):
  for kind in ['fifo','symlink','changed']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'source';p.write_bytes(b'owned ascii');realopen=os.open;realread=os.read;fds=[]
    def opened(*args,**kwargs):
     if kind!='changed':
      p.unlink()
      if kind=='fifo':os.mkfifo(p)
      else:p.symlink_to(Path(tmp)/'target');(Path(tmp)/'target').write_bytes(b'valid')
     fd=realopen(*args,**kwargs);fds.append(fd);return fd
    def read(*args,**kwargs):
     if kind=='changed':p.write_bytes(b'changed source length')
     return realread(*args,**kwargs)
    with patch.object(cli.os,'open',side_effect=opened),patch.object(cli.os,'read',side_effect=read):
     with self.assertRaises((ValueError,OSError)):cli.read_source(p)
    for fd in fds:
     with self.assertRaises(OSError):os.fstat(fd)
 def test_resealed_faults(self):
  for fault in ['wait','timeout','reaped','cache','error','target']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/source-cli-input-2026-10-11',e);p=e/'fixed/process/result.json';d=json.loads(p.read_text());row=d['records'][0]
    if fault=='wait':row['wait']['code']=0
    elif fault=='timeout':row['wait']['timeout']=True
    elif fault=='reaped':row['wait']['reaped']=False
    elif fault=='cache':row['cache_created']=True
    elif fault=='error':row['stderr']=json.dumps({'ok':True})
    else:(e/'fixed/process/symlink/target.swift').write_bytes(b'changed')
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='9947e70f8e29c102424b187bd59e5f090cdb1c7ffea11ae6dcd37427070eb57e'
