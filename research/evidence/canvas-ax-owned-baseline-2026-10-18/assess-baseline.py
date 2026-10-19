from pathlib import Path
import json,hashlib,os,stat
from decoder import record
p=Path(__file__).resolve().parent;plan=json.loads((p/'experiment.json').read_text());obs=json.loads((p/'receipt-observation.json').read_text())
expected_binary='/Users/8amps/Library/Developer/Xcode/DerivedData/PreviewLab-aybvehbjrqcwptcgpubkgsryjlxa/Build/Products/Debug/PreviewLab.app/Contents/MacOS/PreviewLab'
filelist='/Users/8amps/Library/Developer/Xcode/DerivedData/PreviewLab-aybvehbjrqcwptcgpubkgsryjlxa/Build/Intermediates.noindex/PreviewLab.build/Debug/PreviewLab.build/Objects-normal/arm64/PreviewLab.SwiftFileList'
def need(v,m):
 if not v:raise ValueError(m)
def bounded(path,limit):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_size<=limit,'file shape');data=os.read(fd,limit+1);need(len(data)==s.st_size,'file length');return data
 finally:os.close(fd)
need(len(obs['records'])==1,'one baseline record');x=obs['records'][0];live=x['live_identity'];need(type(live['pid']) is int and live['state']=='L' and len(live['identity'])==3 and all(type(z) is int for z in live['identity'][:2]) and live['identity'][2]==expected_binary,'live owned identity')
filebytes=bounded(filelist,4096);want_source='/tmp/callback-ui-access-20261018/workspace/Sources/PreviewLab/PreviewLab.swift\n';need(filebytes==want_source.encode(),'exact build source association')
binary=bounded(expected_binary,1024*1024)
identity={'nonce':plan['nonce'],'pid':live['pid'],'view':'96a040cf-c557-4ebd-846c-a00e3b4de71e'};raw=bytes.fromhex(x['raw_hex']);value=record(raw,x['name'],identity,'appear',0,0)
(p/'native-receipt.json').write_bytes(raw)
(p/'build-association.json').write_text(json.dumps({'binary_path':expected_binary,'binary_bytes':len(binary),'binary_sha256':hashlib.sha256(binary).hexdigest(),'filelist_path':filelist,'filelist_utf8':filebytes.decode(),'filelist_sha256':hashlib.sha256(filebytes).hexdigest(),'scope':'Owned file/build association, not loaded-code attestation; binary bytes not published'},indent=2)+'\n')
(p/'assessment.json').write_text(json.dumps({'identity':identity,'record':value,'bytes_compared':len(raw),'live_identity':live,'visual':{'view':identity['view'],'count':0,'callback_title':'Owned callback probe','receipt_error_visible':False,'authority':'Operator read from inline screenshot; screenshot bytes not archived'},'baseline_qualified':True,'input_qualified':False,'general_sandbox_policy_proven':False,'source_selection_causality_proven':False,'private_transport_proven':False},indent=2)+'\n')
print(json.dumps({'baseline_bytes':len(raw),'owned_pid':live['pid'],'view':identity['view'],'source_association':True}))
