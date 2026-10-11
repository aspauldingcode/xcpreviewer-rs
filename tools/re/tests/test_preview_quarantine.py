import hashlib,importlib.util,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('quarantine_reader',Path(__file__).with_name('verify_preview_quarantine.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class QuarantineTests(unittest.TestCase):
 def test_seal_and_current_sources(self):
  e=ROOT/'research/evidence/mcp-quarantine-2026-10-11';self.assertEqual(reader.verify(e)['complete_bytes'],98304)
  for name in ['preview_consumer.js','preview_readiness.js']:self.assertEqual((ROOT/'tools/re/reloop'/name).read_bytes(),(e/'fixed/runtime'/name).read_bytes())
 def test_resealed_semantic_faults(self):
  for kind in ['wait','worker','readiness','revision','calls','close','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/mcp-quarantine-2026-10-11',e);root=e/'fixed/0';p=root/'result.json';d=json.loads(p.read_text())
    if kind=='wait':(root/'wait.json').write_text(json.dumps({'code':1,'stderr':'','stdout':'','timeout':False}))
    elif kind=='worker':d['raw_status']['lifecycle']['liveWorkers']=1
    elif kind=='readiness':d['raw_status']['readiness']['state']='ready'
    elif kind=='revision':d['states'][-1]['frame']['revision']=1
    elif kind=='calls':d['packets'][6]['name']='frame'
    elif kind=='close':d['final']['lifecycle']['timers']=1
    else:
     b=bytearray((root/'recovered.raw').read_bytes());b[4 if kind=='padding' else 16383]^=1;(root/'recovered.raw').write_bytes(b)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
