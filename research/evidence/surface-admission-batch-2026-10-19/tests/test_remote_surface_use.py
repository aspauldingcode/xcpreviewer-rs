import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('remote_use_reader',Path(__file__).with_name('verify_remote_surface_use.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RemoteSurfaceUseTests(unittest.TestCase):
 def test_seal_full_allocations_and_fixture(self):
  e=ROOT/'research/evidence/remote-surface-use-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocations'],15)
  for name in ['remote_use_probe.c','reuse_primitives.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re/fixtures/RemoteSurfaceUse'/name).read_bytes(),(e/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','timeout','parent-owner','right','audit','alias','peer-signal','peer-exit','lookup','local-remote','lost-parent','global-remote','global-final','peer-clean','cleanup','missing','active','padding','tail']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/remote-surface-use-2026-10-11',e);p=e/'wait.json';d=json.loads(p.read_text());rows=[json.loads(x) for x in d['stdout'].splitlines()];row=rows[1];q=e/'abrupt/peer.json';peer=json.loads(q.read_text())
    if fault=='exit':d['code']=3
    elif fault=='timeout':d['timeout']=True
    elif fault=='parent-owner':row['parent_cf_owner_released']=False
    elif fault=='right':peer['imported_right_released']=False
    elif fault=='audit':peer['audit_peer_verified']=False
    elif fault=='alias':peer['local_use_count']=0
    elif fault=='peer-signal':row['peer_signal']=0
    elif fault=='peer-exit':rows[0]['peer_exit']=42
    elif fault=='lookup':row['lookup_after_all_release']=True
    elif fault=='local-remote':row['local_use_counts'][0]=1
    elif fault=='lost-parent':row['local_use_counts'][2]=0
    elif fault=='global-remote':row['global_in_use'][0]=0
    elif fault=='global-final':row['global_in_use'][3]=1
    elif fault=='peer-clean':(e/'clean/peer-clean.json').write_text(json.dumps({'local_use_count':0,'global_in_use':False,'explicit_decrement':True}))
    elif fault=='cleanup':row['peer_endpoint_name_removed']=False
    elif fault=='missing':(e/'abrupt/parent-after-decrement.bin').unlink()
    else:
     f=e/'abrupt/parent-after-peer.bin';raw=bytearray(f.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[fault]]^=1;f.write_bytes(raw)
    d['stdout']='\n'.join(json.dumps(x) for x in rows)+'\n';p.write_text(json.dumps(d));q.write_text(json.dumps(peer));(e/'manifest.json').write_text(json.dumps({'files':{str(f.relative_to(e)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in e.rglob('*') if f.is_file() and f.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='e8eeac29bdc5f78ff87070ab5f8c2ec8b193b8fed4241570f276edca4d1cde9b'
