import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('remote_alias_reader',Path(__file__).with_name('verify_remote_surface_alias.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RemoteSurfaceAliasTests(unittest.TestCase):
 def test_seal_full_allocations_and_fixture(self):
  e=ROOT/'research/evidence/remote-surface-alias-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocations'],140)
  for name in ['remote_alias_probe.c','reuse_primitives.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re/fixtures/RemoteSurfaceAlias'/name).read_bytes(),(e/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','timeout','parent-owner','right','audit','alias','peer-signal','peer-exit','global','recurrence','held-id','cleanup','missing','active','padding','tail','stale-old']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/remote-surface-alias-2026-10-11',e);p=e/'wait.json';d=json.loads(p.read_text());rows=[json.loads(x) for x in d['stdout'].splitlines()];row=rows[1];q=e/'abrupt/peer.json';peer=json.loads(q.read_text())
    if fault=='exit':d['code']=3
    elif fault=='timeout':d['timeout']=True
    elif fault=='parent-owner':row['parent_cf_owner_released']=False
    elif fault=='right':peer['imported_right_released']=False
    elif fault=='audit':peer['audit_peer_verified']=False
    elif fault=='alias':peer['cf_alias_retained']=False
    elif fault=='peer-signal':row['peer_signal']=0
    elif fault=='peer-exit':rows[0]['peer_exit']=42
    elif fault=='global':row['lookup_after_peer']=True
    elif fault=='recurrence':row['after_ids'][0]=row['old_id']+1
    elif fault=='held-id':row['held_ids'][0]=row['old_id']
    elif fault=='cleanup':row['peer_endpoint_name_removed']=False
    elif fault=='missing':(e/'abrupt/held-candidate-063.bin').unlink()
    elif fault=='stale-old':shutil.copyfile(e/'abrupt/initial.bin',e/'abrupt/stale-lookup.bin')
    else:
     f=e/'abrupt/peer-after-churn.bin';raw=bytearray(f.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[fault]]^=1;f.write_bytes(raw)
    d['stdout']='\n'.join(json.dumps(x) for x in rows)+'\n';p.write_text(json.dumps(d));q.write_text(json.dumps(peer));(e/'manifest.json').write_text(json.dumps({'files':{str(f.relative_to(e)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in e.rglob('*') if f.is_file() and f.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='c1c3eac29bcb10978a1e81fadd1b9330393df9ac5812350dd0da99db3b04d86d'
