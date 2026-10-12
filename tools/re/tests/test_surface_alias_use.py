import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('alias_use_reader',Path(__file__).with_name('verify_surface_alias_use.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class SurfaceAliasUseTests(unittest.TestCase):
 def test_seal_full_allocations_and_fixture(self):
  e=ROOT/'research/evidence/surface-alias-use-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['allocations'],34)
  for name in ['alias_use_probe.c','surface_ipc_probe.c']:self.assertEqual((ROOT/'tools/re/fixtures/SurfaceAliasUse'/name).read_bytes(),(e/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','timeout','same-process','same-wrapper','name','owner','balance','lookup','local-alias','global-two','drop-alias','last-decrement','stage','missing','active','padding','tail']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/surface-alias-use-2026-10-11',e);p=e/'repeat-1/wait.json';d=json.loads(p.read_text());row=json.loads(d['stdout'])
    if fault=='exit':d['code']=3
    elif fault=='timeout':d['timeout']=True
    elif fault=='same-process':row['pid']=json.loads(json.loads((e/'repeat-0/wait.json').read_text())['stdout'])['pid']
    elif fault=='same-wrapper':row['equal_refs'][0]=True
    elif fault=='name':row['resource_name_removed']=False
    elif fault=='owner':row['all_cf_owners_released']=False
    elif fault=='balance':row['balanced_use_calls']=False
    elif fault=='lookup':row['lookup_after_release']=True
    elif fault=='local-alias':row['samples'][1]['local'][0]=0
    elif fault=='global-two':row['samples'][2]['global'][0]=2
    elif fault=='drop-alias':row['samples'][4]['local'][0]=0
    elif fault=='last-decrement':row['samples'][5]['global'][1]=1
    elif fault=='stage':row['samples'][3]['stage']=4
    elif fault=='missing':(e/'repeat-1/stage-6-alias-0.bin').unlink()
    else:
     f=e/'repeat-1/stage-4-alias-1.bin';raw=bytearray(f.read_bytes());raw[{'active':0,'padding':68,'tail':16383}[fault]]^=1;f.write_bytes(raw)
    d['stdout']=json.dumps(row)+'\n';p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(f.relative_to(e)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in e.rglob('*') if f.is_file() and f.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='be5fc8e52f69d8d754817afce5e655b918977f078faac4fdd675390c4d7abc3f'
