import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
from reloop import sourcecache
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('payload_reader',Path(__file__).with_name('verify_cache_payload.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CachePayloadTests(unittest.TestCase):
 def test_sealed_controls_and_current_source(self):
  e=ROOT/'research/evidence/cache-payload-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['complete_module_bytes'],120)
 def test_declared_payload_limits(self):
  root=ROOT/'research/evidence/cache-payload-2026-10-11/fixed/view.ll';receipt=json.loads((root/'before.json').read_text())['receipt'];original=root/'output/versions'/receipt['entry_sha256']
  for name,limit in {'view.c':65536,'view.ll':4194304,'view.wasm':4194304}.items():
   for value in [-1,True,limit+1]:
    with self.subTest(name=name,value=value),tempfile.TemporaryDirectory() as tmp:
     folder=Path(tmp)/'entry';shutil.copytree(original,folder);m=json.loads((folder/'manifest.json').read_text());m['files'][name]['bytes']=value;raw=json.dumps(m).encode();(folder/'manifest.json').write_bytes(raw)
     with self.assertRaisesRegex(ValueError,'Cache payload size limit'):sourcecache.entry(folder,m['cache_key'],m['identity'],hashlib.sha256(raw).hexdigest())
 def test_resealed_faults(self):
  for fault in ['wait','timeout','reaped','calls','publication','module']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/cache-payload-2026-10-11',e);root=e/'fixed/view.wasm';p=root/'wait.json';wait=json.loads(p.read_text());q=root/'after.json';after=json.loads(q.read_text())
    if fault=='wait':wait['code']=1
    elif fault=='timeout':wait['timeout']=True
    elif fault=='reaped':wait['reaped']=False
    elif fault=='calls':after['calls'].append(['extra compiler'])
    elif fault=='publication':after['pointer_hex']='00'
    else:after['module_hex']=('01'+after['module_hex'][2:])
    p.write_text(json.dumps(wait));q.write_text(json.dumps(after));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='4c3f7c445ce0d3faec6edb334d7e104b14f90d4aba16f909aa8194a1cc2de9f7'
