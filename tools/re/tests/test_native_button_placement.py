import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('placement_reader',Path(__file__).with_name('verify_native_button_placement.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class NativeButtonPlacementTests(unittest.TestCase):
 def test_failed_acquisition_seal_and_fixture(self):
  e=ROOT/'research/evidence/native-button-placement-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e),{'native_failures':2,'frame_bytes_observed':0,'input_acceptance':False});self.assertEqual((ROOT/'tools/re/fixtures/PlacementButtonPressReference.swift').read_bytes(),(e/'PlacementButtonPressReference.swift').read_bytes())
 def test_resealed_false_acceptance(self):
  for kind in ['exit','timeout','diagnostic','fabricated_result','fabricated_frame','cleanup','acceptance']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/native-button-placement-2026-10-11',e);root=e/'run-0';p=root/'wait.json';d=json.loads(p.read_text())
    if kind=='exit':d['code']=0
    elif kind=='timeout':d['timeout']=True
    elif kind=='diagnostic':d['stderr']=d['stderr'].replace('Code=3','Code=2')
    elif kind=='fabricated_result':(root/'result.json').write_text('{}')
    elif kind=='fabricated_frame':(root/'initial.raw').write_bytes(bytes(16384))
    else:
     q=e/'assessment.json';a=json.loads(q.read_text());a['cleanup_verified' if kind=='cleanup' else 'input_acceptance']=True;q.write_text(json.dumps(a))
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='fa01891281b3b6a05f98475c983ebb2bdb0c4d0d02dd83b6389816025adc6644'
