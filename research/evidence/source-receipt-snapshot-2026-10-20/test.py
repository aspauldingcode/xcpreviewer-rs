from pathlib import Path
import os,subprocess
w=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');env=os.environ.copy();env['PYTHONPATH']=str(r/'tools/re')+':'+str(r/'tools/re/tests')
code="import unittest; names=['test_sourcereceiptsnapshot','test_sourcerevision','test_sourcefileloop','test_livewasmhost','test_livecorpus']; suite=unittest.defaultTestLoader.loadTestsFromNames(names); result=unittest.TextTestRunner(verbosity=2).run(suite); raise SystemExit(not result.wasSuccessful())"
p=subprocess.run(['python3','-c',code],cwd=r,capture_output=True,env=env,timeout=60);(w/'tests.log').write_bytes(p.stdout+p.stderr);print((p.stdout+p.stderr).decode()[-2200:]);p.check_returncode()
