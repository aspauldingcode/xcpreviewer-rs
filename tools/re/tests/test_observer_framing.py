import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('framing_reader',Path(__file__).with_name('verify_observer_framing.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class ObserverFramingTests(unittest.TestCase):
    def test_actual_owned_segmentation_and_every_payload_byte(self):
        result=reader.verify(ROOT/'research/evidence/observer-framing-2026-10-10');self.assertTrue(result['utf8_preserved']);self.assertGreater(result['paired_payload_bytes'],400)
    def test_resealed_false_encoding_and_byte_claims(self):
        for kind in ['scope','accept','payload']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/observer-framing-2026-10-10',folder)
                name='after/ascii-bytewise/owned-supervisor' if kind=='payload' else 'after/result.json';p=folder/name
                if kind=='payload':p.write_text(p.read_text().replace('[123]','[124]',1))
                else:
                    d=json.loads(p.read_text())
                    if kind=='scope':d['controls'][0]['record']['report']['scope']='owned-?'
                    else:d['controls'][1]['error']=None
                    p.write_text(json.dumps(d))
                m=json.loads((folder/'manifest.json').read_text());m['files'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises((AssertionError,TypeError)):reader.verify(folder)
