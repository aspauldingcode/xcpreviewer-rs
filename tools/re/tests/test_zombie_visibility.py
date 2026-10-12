import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from verify_zombie_visibility import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/zombie-visibility-2026-10-11'
class ZombieVisibilityTests(unittest.TestCase):
 def test_seal_fixture_reader(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['unreaped_and_reaped_rows_both_absent']);self.assertEqual((ROOT/'tools/re/fixtures/ZombieVisibility/main.c').read_bytes(),(E/'main.c').read_bytes())
 def test_resealed_faults(self):
  for fault in ['root','waitid','reaped','signal','positive','parent','birth','path','byte','helper','budget','missing-phase']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e)
    if fault in ['root','waitid','reaped','signal','positive']:
     p=e/'result.json';d=json.loads(p.read_text())
     if fault=='root':d['root_exit_code']=1
     elif fault=='waitid':d['unreaped']['exited']=False
     elif fault=='reaped':d['reaped']['exit_code']=0
     elif fault=='signal':d['signals']=[9]
     else:d['zombie_row_present']=True
    elif fault=='byte':p=e/'child.bin';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault in ['helper','budget']:
     p=e/'environment.json';d=json.loads(p.read_text())
     if fault=='helper':d['helper_sha256']='0'*64
     else:d['budgets']['native_subprocesses']=5
    else:
     p=e/'samples.json';d=json.loads(p.read_text());child=next(iter(d[1]['known']))
     if fault=='parent':d[0]['rows'][child]['parent']+=1
     elif fault=='birth':d[1]['known'][child][0]+=1
     elif fault=='path':d[0]['rows'][child]['identity'][2]='/wrong'
     else:d.pop()
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
SEAL='cf7b7989575232917c9ddbacad3176887e5d8f3d0b2b67812fb539fa5af3edd1'
