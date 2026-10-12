import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('capped_reader',Path(__file__).with_name('verify_admitted_build.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class AdmittedBuildTests(unittest.TestCase):
 def test_sealed_real_build_and_runtime(self):
  e=ROOT/'research/evidence/admitted-build-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocation_bytes'],131072);self.assertEqual((ROOT/'tools/re/reloop/sourcecache.py').read_bytes(),(e/'sourcecache.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['cold','hit','calls','cap','group','admission-present','admission-signal','admission-pid','v8','wasmkit','active','padding','tail','invalid','native']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/admitted-build-2026-10-11',e)
    if fault in ['cold','hit','calls','cap','group','admission-present','admission-signal','admission-pid']:
     p=e/'build.json';d=json.loads(p.read_text())
     if fault=='cold':d['cold']['cache_hit']=True
     elif fault=='hit':d['hit']['cache_hit']=False
     elif fault=='calls':d['calls'].append(d['calls'][0])
     elif fault=='admission-present':d['group_checks'][0]['outcome']='present'
     elif fault=='admission-signal':d['group_checks'][0]['signal']=9
     elif fault=='admission-pid':d['group_checks'][0]['pid']+=1
     elif fault=='group':d['calls'][0]['group']+=1
     else:d['calls'][0]['preexec_present']=False
     p.write_text(json.dumps(d))
    elif fault in ['v8','wasmkit']:
     p=e/(fault+'-wait.json');d=json.loads(p.read_text());d['code']=1;p.write_text(json.dumps(d))
    else:
     p=e/('native-callback.raw' if fault=='native' else 'invalid-0-0.raw' if fault=='invalid' else 'frame-0-1-0.raw');raw=bytearray(p.read_bytes());raw[68 if fault=='padding' else -1 if fault=='tail' else 0]^=1;p.write_bytes(raw)
    (e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)



SEAL='c1045383941a2d64985e0a0b4a983af25cc99b07d6f08ba45b32ce8ac6e47b48'
