import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('success_reader',Path(__file__).with_name('verify_compiler_success_descendant.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CompilerSuccessDescendantTests(unittest.TestCase):
 def test_seal_and_owned_source(self):
  e=ROOT/'research/evidence/compiler-success-descendant-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertFalse(reader.verify(e)['normal_success_descendant_quiescence']);self.assertEqual((ROOT/'tools/re/fixtures/CompilerSuccessDescendant/emitter.py').read_bytes(),(e/'emitter.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['root-exit','root-stderr','late-return','unfinished','root-identity','child-identity','no-growth','first-byte','later-byte','final-byte','failure-hidden','false-repeat']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/compiler-success-descendant-2026-10-11',e);p=e/'repeat-1/wait.json';d=json.loads(p.read_text());row=json.loads(d['root_stdout']);q=e/'repeat-1/child-finished.json';done=json.loads(q.read_text())
    if fault=='root-exit':d['root_code']=1
    elif fault=='root-stderr':d['root_stderr']='failed'
    elif fault=='late-return':d['root_elapsed_seconds']=2
    elif fault=='unfinished':done['self_terminated']=False
    elif fault=='root-identity':row['process_group']+=1
    elif fault=='child-identity':row['child_pid']+=1
    elif fault=='no-growth':shutil.copyfile(e/'repeat-1/at-return.bin',e/'repeat-1/after-return.bin');d['later_bytes']=1
    elif fault=='failure-hidden':(e/'harness-failure.json').unlink()
    elif fault=='false-repeat':(e/'repeat-0/wait.json').write_text(json.dumps(d))
    else:
     f=e/'repeat-1'/({'first-byte':'at-return.bin','later-byte':'after-return.bin','final-byte':'heartbeat.bin'}[fault]);raw=bytearray(f.read_bytes());raw[-1]^=1;f.write_bytes(raw)
    d['root_stdout']=json.dumps(row);p.write_text(json.dumps(d));q.write_text(json.dumps(done));(e/'manifest.json').write_text(json.dumps({'files':{str(f.relative_to(e)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in e.rglob('*') if f.is_file() and f.name!='manifest.json'}}))
    with self.assertRaises((AssertionError,FileNotFoundError)):reader.verify(e)

SEAL='fdeb1ea6146620340d79c5450dacfd19b3eb1cc7f56c3563537437d2bb9afad6'
