import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('adoption_reader',Path(__file__).with_name('verify_graph_adoption.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class GraphAdoptionEvidenceTests(unittest.TestCase):
 def test_seal_and_current_adopter(self):
  e=ROOT/'research/evidence/graph-adoption-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['fresh_declared_checks'],88);self.assertEqual((ROOT/'tools/re/reloop/graphloop.py').read_bytes(),(e/'graphloop.py').read_bytes())
 def test_resealed_false_promotion(self):
  for fault in ['anchor','contract','valid','present','passed','actual','delivery','milestone','candidate']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/graph-adoption-2026-10-11',e);p=e/'adoption.json';a=json.loads(p.read_text());q=e/'frontier.json';f=json.loads(q.read_text())
    if fault=='anchor':a['manifest_sha256']='0'*64
    elif fault=='contract':a['experiment_hash']='0'*64
    elif fault=='valid':a['verification']['valid']=False
    elif fault=='present':a['verification']['checks'][0]['present']=False
    elif fault=='passed':a['verification']['checks'][0]['passed']=False
    elif fault=='actual':a['verification']['checks'][0]['actual']=0
    elif fault=='delivery':a['delivery_review']='accepted'
    elif fault=='milestone':f['all_milestones_complete']=True
    else:f['candidates']=[{'task':'completed','state':'ready'}]
    p.write_text(json.dumps(a));q.write_text(json.dumps(f));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='d9b2750ce070f5b79ccb9a949b25baf46d2800934d28b378bb6d3025dd061601'
