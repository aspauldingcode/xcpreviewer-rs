"""Post-acquisition independent provider-byte faults with hashes recomputed."""
import importlib.util,json,hashlib,tempfile,unittest
from pathlib import Path
from admit import admitted
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('synthetic_controls',P/'test-admit.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ProviderReseal(unittest.TestCase):
 def test_provider_pixels_and_padding_despite_resealed_hashes(self):
  for route,offset in [(0,0),(0,1024),(1,12479)]:
   with self.subTest(route=route,offset=offset),tempfile.TemporaryDirectory() as tmp:
    r=Path(tmp);module.Controls().fixture(r);f=r/'owned-documents'/('route%d-provider.raw'%route);raw=bytearray(f.read_bytes());raw[offset]^=1;f.write_bytes(raw)
    f=r/'fixture-record.json';v=json.loads(f.read_text());rows=[json.loads(x) for x in v['record']['stdout'].splitlines()];rows[route]['provider_sha256']=hashlib.sha256(raw).hexdigest();s=''.join(json.dumps(x)+'\n' for x in rows);v['record'].update(stdout=s,stdoutBytes=len(s.encode()),stdoutSha256=hashlib.sha256(s.encode()).hexdigest());f.write_text(json.dumps(v))
    with self.assertRaises(ValueError):admitted(r)
if __name__=='__main__':unittest.main()
