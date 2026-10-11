import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('capped_reader',Path(__file__).with_name('verify_capped_build.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CappedBuildTests(unittest.TestCase):
 def test_sealed_real_build_and_runtime(self):
  e=ROOT/'research/evidence/capped-build-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocation_bytes'],131072);self.assertEqual((ROOT/'tools/re/reloop/sourcecache.py').read_bytes(),(e/'sourcecache.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['cold','hit','calls','cap','v8','wasmkit','active','padding','tail','invalid','native']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/capped-build-2026-10-11',e)
    if fault in ['cold','hit','calls','cap']:
     p=e/'build.json';d=json.loads(p.read_text())
     if fault=='cold':d['cold']['cache_hit']=True
     elif fault=='hit':d['hit']['cache_hit']=False
     elif fault=='calls':d['calls'].append(d['calls'][0])
     else:d['calls'][0]['preexec_present']=False
     p.write_text(json.dumps(d))
    elif fault in ['v8','wasmkit']:
     p=e/(fault+'-wait.json');d=json.loads(p.read_text());d['code']=1;p.write_text(json.dumps(d))
    else:
     p=e/('native-callback.raw' if fault=='native' else 'invalid-0-0.raw' if fault=='invalid' else 'frame-0-1-0.raw');raw=bytearray(p.read_bytes());raw[68 if fault=='padding' else -1 if fault=='tail' else 0]^=1;p.write_bytes(raw)
    (e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='1f6e25a20d655446e75b0a1327d348aecb10d62c1880f00f8f66538a4c362d6d'
