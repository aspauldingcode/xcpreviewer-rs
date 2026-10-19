from pathlib import Path
import importlib.util,json,sys
p=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('matrix',p/'test_surface_full_failure_admission.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
print(json.dumps(m.run(p/(sys.argv[1]+'.py'),Path('/Users/8amps/xcpreviewer-rs/research/evidence/surface-full-failure-2026-10-11'))))
