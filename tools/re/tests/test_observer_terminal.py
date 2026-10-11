import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('terminal_reader',Path(__file__).with_name('verify_observer_terminal.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class ObserverTerminalTests(unittest.TestCase):
    def test_owned_protocol_and_actual_reparent_abort(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/observer-terminal-2026-10-10')['previous_false_acceptances'],4)
    def test_resealed_false_publication_release_and_identity_claims(self):
        for kind in ['publish','release','identity','trailer']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/observer-terminal-2026-10-10',folder)
                name='after/result.json' if kind=='trailer' else 'cancel-fixed/result.json';p=folder/name;d=json.loads(p.read_text())
                if kind=='publish':d['error']=None
                elif kind=='release':d['record']['report']['remaining_observed']=1
                elif kind=='identity':d['reparented']['identity'][1]+=1
                else:d['controls'][1]['error']=None
                p.write_text(json.dumps(d));m=json.loads((folder/'manifest.json').read_text());m['files'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises((AssertionError,TypeError)):reader.verify(folder)
