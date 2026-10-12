import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('seed_reader',Path(__file__).with_name('verify_surface_seed_timing.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SurfaceSeedTimingTests(unittest.TestCase):
 def test_seal_full_allocations_and_fixture(self):
  e=ROOT/'research/evidence/surface-seed-timing-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocations'],52)
  for name in ['seed_timing_probe.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re/fixtures/SurfaceSeedTiming'/name).read_bytes(),(e/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','timeout','same-process','same-wrapper','name','owner','lookup','lock-before','noop-seed','readonly-seed','alias-seed','resource-id','unlock-code','missing','active','padding','tail','restore','inside-before','alias-before','inside-after','locked-before','locked-after']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/surface-seed-timing-2026-10-11',e);p=e/'repeat-1/wait.json';d=json.loads(p.read_text());row=json.loads(d['stdout'])
    if fault=='exit':d['code']=3
    elif fault=='timeout':d['timeout']=True
    elif fault=='same-process':row['pid']=json.loads(json.loads((e/'repeat-0/wait.json').read_text())['stdout'])['pid']
    elif fault=='same-wrapper':row['distinct_alias']=False
    elif fault=='name':row['resource_name_removed']=False
    elif fault=='owner':row['all_cf_owners_released']=False
    elif fault=='lookup':row['lookup_after_release']=True
    elif fault=='lock-before':row['steps'][1]['lock_seed']=row['steps'][1]['before']
    elif fault=='noop-seed':row['steps'][1]['after']=1
    elif fault=='readonly-seed':row['steps'][0]['after']=2
    elif fault=='alias-seed':row['steps'][2]['alias_after']=2
    elif fault=='resource-id':row['steps'][3]['surface_id']+=1
    elif fault=='unlock-code':row['steps'][4]['unlock_code']=3
    elif fault=='missing':(e/'repeat-1/stage-6-alias-0.bin').unlink()
    elif fault=='inside-before':row['steps'][2]['inside_before']=row['steps'][2]['before']
    elif fault=='alias-before':row['steps'][3]['alias_inside_before']=row['steps'][3]['before']
    elif fault=='inside-after':row['steps'][4]['inside_after']+=1
    elif fault=='locked-before':shutil.copyfile(e/'repeat-1/locked-after-2.bin',e/'repeat-1/locked-before-2.bin')
    elif fault=='locked-after':shutil.copyfile(e/'repeat-1/locked-before-2.bin',e/'repeat-1/locked-after-2.bin')
    elif fault=='restore':shutil.copyfile(e/'repeat-1/stage-5-alias-0.bin',e/'repeat-1/stage-6-alias-0.bin')
    else:
     f=e/'repeat-1/stage-2-alias-1.bin';raw=bytearray(f.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[fault]]^=1;f.write_bytes(raw)
    d['stdout']=json.dumps(row)+'\n';p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(f.relative_to(e)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in e.rglob('*') if f.is_file() and f.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='e99a7333b9d7bad045a91b3919e0ebbd5a02a31bf4073e9c01d4d2d23e4b0be1'
