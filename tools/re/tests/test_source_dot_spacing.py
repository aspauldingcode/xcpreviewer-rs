import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('space_reader',Path(__file__).with_name('verify_source_dot_spacing.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SourceDotSpacingTests(unittest.TestCase):
 def test_external_seal(self):
  e=ROOT/'research/evidence/source-dot-spacing-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['accepted_expressions'],2)
 def test_current_lowerers_preserve_measured_controls(self):
  from reloop import primarysource,viewsource
  e=ROOT/'research/evidence/source-dot-spacing-2026-10-11'
  for row in json.loads((e/'observations.json').read_text()):
   for name,parser in [('primary',primarysource),('opaque',viewsource)]:
    if row['index']==0:self.assertEqual(parser.parse(row['cases'][name]),row['baseline_configs'][name])
    else:
     with self.assertRaises(ValueError):parser.parse(row['cases'][name])
 def test_resealed_faults(self):
  for fault in ['exit','timeout','missing','source','config','diagnostic','compiler','fixed-accept']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/source-dot-spacing-2026-10-11',e);p=e/'observations.json';rows=json.loads(p.read_text())
    if fault=='exit':rows[1]['wait']['code']=0
    elif fault=='timeout':rows[1]['wait']['timeout']=True
    elif fault=='missing':rows.pop()
    elif fault=='source':(e/'control-1.swift').write_bytes((e/'control-1.swift').read_bytes().replace(b'. frame',b'.frame'))
    elif fault=='config':rows[1]['baseline_configs']['primary']['alphas'][0]=8
    elif fault=='fixed-accept':
     q=e/'fixed/observations.json';d=json.loads(q.read_text());d[1]['results']['primary']['accepted']=True;q.write_text(json.dumps(d))
    elif fault=='diagnostic':(e/'control-1.stderr').write_text('native error')
    else:
     q=e/'environment.json';env=json.loads(q.read_text());env['compiler_sha256']='0'*64;q.write_text(json.dumps(env))
    p.write_text(json.dumps(rows));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='9ba850dce7f02852eefb449a2b0996a8cb19cae1c5297170c4c716c220b7fab7'
