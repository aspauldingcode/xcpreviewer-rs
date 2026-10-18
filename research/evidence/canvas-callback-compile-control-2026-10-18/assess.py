import sys,json
from pathlib import Path
p=Path(__file__).resolve().parent
from decoder import directory,canonical,expected,filename
run=json.loads((p/'runtime-positive/execution.json').read_text());starts=[e for e in run['events'] if e['event']=='process_started']
if len(starts)!=1:raise ValueError('Missing parent PID')
identity={'nonce':'60fd2da461f6404ea93e47eb59d6831a','pid':starts[0]['pid'],'view':'01234567-89ab-cdef-0123-456789abcdef'}
records=directory(p/'native-receipts/positive',identity,3)
files={f.name:f.read_bytes().hex() for f in (p/'native-receipts/positive').iterdir()}
result={'identity':identity,'files_hex':files,'bytes_compared':sum(len(bytes.fromhex(x)) for x in files.values()),'actual_wait':run['result'],'runtime_control_accepted':False,'duplicate_started':False,'native_button_input':False,'ui_sessions':0,'failure':'Controller observer reported OSError: Cannot observe a live owned root; execution failed despite eventual wait0 and four exact retained records. No retry.','unknown':'The sampled observer error narrows the failed gate; full process-observation ordering and fast-exit race causality remain unverified.'}
(p/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'bytes_compared':result['bytes_compared'],'runtime_control_accepted':False}))
