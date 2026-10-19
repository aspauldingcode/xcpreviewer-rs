import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('carrier_reader',Path(__file__).with_name('verify_gpu_event_carrier.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CarrierTests(unittest.TestCase):
 def test_carrier_and_gated_bytes(self):
  e=ROOT/'research/evidence/gpu-event-carrier-2026-10-11';self.assertEqual((ROOT/'tools/re/gpu_event_carrier.m').read_bytes(),(e/'gpu_event_carrier.m').read_bytes());self.assertEqual(reader.verify(e)['complete_bytes'],131072)
 def test_resealed_archive_identity_order_completion_and_padding(self):
  for kind in ['wait','archive','identity','wrong','completion','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/gpu-event-carrier-2026-10-11',e);p=e/'result-0.json';d=json.loads(p.read_text())
    if kind=='wait':(e/'wait-0.json').write_text(json.dumps({'code':1,'timeout':False,'stderr':''}))
    elif kind=='archive':d['archive']['produced_data']=True
    elif kind=='identity':d['reply']['pid']+=1
    elif kind=='wrong':d['reply']['after_wrong']=99
    elif kind=='completion':d['completion_status']=0
    else:
     b=bytearray(base64.b64decode(d['after']));b[44 if kind=='padding' else 16383]^=1;d['after']=base64.b64encode(b).decode()
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
