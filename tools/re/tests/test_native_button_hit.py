import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('native_state_reader',Path(__file__).with_name('verify_native_button_hit.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class NativeButtonHitTests(unittest.TestCase):
 def test_seal_full_bytes_and_current_fixture(self):
  e=ROOT/'research/evidence/native-button-hit-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocation_bytes'],32768);self.assertEqual((ROOT/'tools/re/fixtures/HitButtonPressReference.swift').read_bytes(),(e/'HitButtonPressReference.swift').read_bytes())
 def test_resealed_faults(self):
  for kind in ['wait','callbacks','button','press','windows','visibility','key','navigation','hit','point','active','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/native-button-hit-2026-10-11',e);root=e/'run-0';p=root/'result.json';d=json.loads(p.read_text())
    if kind=='wait':(root/'wait.json').write_text(json.dumps({'code':1,'timeout':False,'stdout':'','stderr':''}))
    elif kind=='callbacks':d['rows'][0]['callbacks']=0
    elif kind=='button':d['button_found']=True
    elif kind=='press':d['presses']=[{'accepted':True}]
    elif kind=='visibility':d['visible']['visible']=False
    elif kind=='key':d['visible']['key']=True
    elif kind=='navigation':d['navigation']['roles']=['AXButton']
    elif kind=='hit':d['hit']['returned']=False
    elif kind=='point':d['hit']['screen_point']=[80,30]
    elif kind=='windows':d['owned_windows']=1
    else:
     q=root/'initial.raw';raw=bytearray(q.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[kind]]^=1;q.write_bytes(raw)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='e4cb717e386563a6665b5f39a5c1e20f77162cada960f31756dccf6120b14a63'
