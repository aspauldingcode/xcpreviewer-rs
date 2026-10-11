import copy,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
from reloop.observed_group_anchor import parse_snapshot
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('schema_reader',Path(__file__).with_name('verify_observer_schema.py'))
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
class ObserverSchemaTests(unittest.TestCase):
    def test_whole_response_before_signal_gate(self):
        row={'pid':123,'parent':0,'group':123,'state':'L','identity':[0,999999,'/owned']}
        self.assertEqual(parse_snapshot(json.dumps([row]))[123]['identity'],(0,999999,'/owned'))
        bad=[]
        for key,value in [('pid',True),('pid',2147483648),('parent',-1),('group',None),('group',0),('state','?')]:
            r=copy.deepcopy(row);r['pid']=124;r[key]=value;bad.append([row,r])
        for value in [-1,1000000,True]:
            r=copy.deepcopy(row);r['pid']=124;r['identity'][1]=value;bad.append([row,r])
        r=copy.deepcopy(row);del r['group'];bad.append([r])
        bad.extend([[row,row],{},[row]*257])
        for data in bad:
            with self.subTest(data=data),self.assertRaises(AssertionError):parse_snapshot(json.dumps(data))
    def test_actual_owned_before_after_controls(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/observer-schema-2026-10-10')['prior_false_acceptances'],3)
    def test_resealed_false_cleanup_and_status_claims(self):
        for kind in ['drain','status','before']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/observer-schema-2026-10-10',folder)
                name='before/result.json' if kind=='before' else 'after/result.json';p=folder/name;d=json.loads(p.read_text())
                if kind=='drain':d['controls'][0]['record']['report']['drained']=True
                elif kind=='status':d['controls'][0]['record']['report']['target_code']=0
                else:d['controls'][0]['error']='falsified'
                p.write_text(json.dumps(d));m=json.loads((folder/'manifest.json').read_text());m['files'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
