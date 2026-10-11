import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('space_reader',Path(__file__).with_name('verify_source_whitespace.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SourceWhitespaceTests(unittest.TestCase):
 def test_external_seal(self):
  e=ROOT/'research/evidence/source-whitespace-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['accepted_expressions'],8)
 def test_current_lowerers_preserve_measured_controls(self):
  from reloop import primarysource,viewsource
  e=ROOT/'research/evidence/source-whitespace-2026-10-11'
  for row in json.loads((e/'observations.json').read_text()):
   for name,parser in [('primary',primarysource),('opaque',viewsource)]:self.assertEqual(parser.parse(row['cases'][name]),row['baseline_configs'][name])
 def test_resealed_faults(self):
  for fault in ['exit','timeout','missing','source','config','diagnostic','compiler']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/source-whitespace-2026-10-11',e);p=e/'observations.json';rows=json.loads(p.read_text())
    if fault=='exit':rows[1]['wait']['code']=1
    elif fault=='timeout':rows[1]['wait']['timeout']=True
    elif fault=='missing':rows.pop()
    elif fault=='source':(e/'control-1.swift').write_bytes((e/'control-1.swift').read_bytes().replace(b'\x0b',b' '))
    elif fault=='config':rows[1]['baseline_configs']['primary']['alphas'][0]=8
    elif fault=='diagnostic':(e/'control-1.stderr').write_text('native error')
    else:
     q=e/'environment.json';env=json.loads(q.read_text());env['compiler_sha256']='0'*64;q.write_text(json.dumps(env))
    p.write_text(json.dumps(rows));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='f11aaeff87e9766ad02ee8a5b48c4ee89893fd932e964f326610fe62c69d9f91'
