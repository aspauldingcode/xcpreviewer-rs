import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('remote_seed_reader',Path(__file__).with_name('verify_surface_stream_close.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SurfaceStreamCloseTests(unittest.TestCase):
 def test_seal_full_allocations_and_fixture(self):
  e=ROOT/'research/evidence/surface-stream-close-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocations'],20)
  for name in ['stream_close_probe.c','reuse_primitives.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re/fixtures/SurfaceStreamClose'/name).read_bytes(),(e/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','timeout','owner','right','audit','peer-exit','peer-signal','lookup','parent-seed','remote-before','remote-after','read-lock','release','identity','cleanup','same-peer','missing','active','padding','tail','premature-edit','stale-after','close-code','close-errno','close-twice','file-pointer','fd','false-ack']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/surface-stream-close-2026-10-11',e);p=e/'wait.json';d=json.loads(p.read_text());rows=[json.loads(x) for x in d['stdout'].splitlines()];row=rows[1];q=e/'fault/peer.json';peer=json.loads(q.read_text());z=e/'fault/stream.json';stream=json.loads(z.read_text())
    if fault=='exit':d['code']=3
    elif fault=='timeout':d['timeout']=True
    elif fault=='owner':row['parent_cf_released']=False
    elif fault=='right':peer['imported_right_released']=False
    elif fault=='audit':peer['audit_peer_verified']=False
    elif fault=='peer-exit':row['peer_exit']=0
    elif fault=='peer-signal':row['peer_signal']=9
    elif fault=='lookup':row['lookup_after_release']=True
    elif fault=='parent-seed':row['lock_seed']=1
    elif fault=='remote-before':peer['observations'][1]['before']=1
    elif fault=='remote-after':peer['observations'][2]['after']=3
    elif fault=='read-lock':peer['observations'][1]['lock_code']=3
    elif fault=='release':peer['cf_alias_released']=False
    elif fault=='identity':peer['surface_id']+=1
    elif fault=='cleanup':row['peer_endpoint_name_removed']=False
    elif fault=='same-peer':row['receiver_pid']=rows[0]['receiver_pid'];peer['pid']=row['receiver_pid']
    elif fault=='close-code':stream['close_code']=0
    elif fault=='close-errno':stream['close_errno']=0
    elif fault=='close-twice':stream['close_calls']=2
    elif fault=='file-pointer':stream['file_pointer_cleared_before_close']=False
    elif fault=='fd':stream['fd_closed']=False
    elif fault=='false-ack':stream['completion_ack_sent']=True
    elif fault=='missing':(e/'fault/peer-stage-4.bin').unlink()
    elif fault=='premature-edit':shutil.copyfile(e/'fault/peer-stage-2.bin',e/'fault/peer-stage-1.bin')
    elif fault=='stale-after':shutil.copyfile(e/'fault/peer-stage-1.bin',e/'fault/peer-stage-2.bin')
    else:
     f=e/'fault/peer-stage-3.bin';raw=bytearray(f.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[fault]]^=1;f.write_bytes(raw)
    d['stdout']='\n'.join(json.dumps(x) for x in rows)+'\n';p.write_text(json.dumps(d));q.write_text(json.dumps(peer));z.write_text(json.dumps(stream));(e/'manifest.json').write_text(json.dumps({'files':{str(f.relative_to(e)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in e.rglob('*') if f.is_file() and f.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='490da0ea73fd4c21c691e0a0566bddd6c9108e67c1b63c5ed01e82e5dc1537f0'
