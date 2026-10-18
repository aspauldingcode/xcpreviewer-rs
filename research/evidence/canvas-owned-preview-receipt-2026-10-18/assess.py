from pathlib import Path
import json
from decoder import record
p=Path(__file__).resolve().parent;plan=json.loads((p/'experiment.json').read_text());obs=json.loads((p/'receipt-observation.json').read_text());build=json.loads((p/'build-association.json').read_text())
if len(obs['records'])!=1:raise ValueError('Expected one record')
x=obs['records'][0];live=x['live_identity'];pid=live['pid'];view='531b00ec-215c-4377-9afe-22f1895e102c'
if type(pid) is not int or live['state']!='L' or live['identity'][2]!=build['binary_path'] or not build['binary_path'].endswith('/Build/Products/Debug/PreviewLab.app/Contents/MacOS/PreviewLab'):raise ValueError('Live identity')
if build['filelist_utf8']!='/tmp/callback-ui-access-20261018/workspace/Sources/PreviewLab/PreviewLab.swift\n':raise ValueError('Build source association')
identity={'nonce':plan['nonce'],'pid':pid,'view':view};raw=bytes.fromhex(x['raw_hex']);value=record(raw,x['name'],identity,'appear',0,0)
(p/'native-receipt.json').write_bytes(raw)
(p/'assessment.json').write_text(json.dumps({'bytes_compared':len(raw),'identity':identity,'record':value,'live_identity':live,'scope':'Owned fixture publication observed; view UUID independently operator-read from inline screenshot, PID/path from public libproc sample, expected nonce from pinned source. Build file list associates executable build root with exact owned source. Not private transport or input causality.','visual_authority':'Operator observation of inline screenshot; screenshot bytes/raw full AX not archived.','button_input_qualified':False,'general_sandbox_policy_proven':False,'source_selection_causality_proven':False},indent=2)+'\n')
print(json.dumps({'bytes_compared':len(raw),'pid':pid,'view':view}))
