import sys,json,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,'tools/re');from reloop.core import Controller,atomic,now
from canvas_graph import read
with Controller().lock():
 d=read('research/loop/continuous.json');prior=d['canvas_evidence_crosswalk_checkpoint'];source=Path(prior['evidence']);assert hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest()==prior['manifest_sha256']
 cross=read(source/'crosswalk.json');pairs=[(doc,link) for doc in cross['documents'] for link in doc['links'] if not link['document_mentions_seal']];assert len(pairs)==2
 def git(*args):return subprocess.run(['git',*args],capture_output=True,check=True,timeout=15).stdout
 anchor=git('rev-parse','origin/master').decode().strip();rows=[]
 for doc,link in pairs:
  name=link['path'];commit=git('log','-1','--format=%H','--',name).decode().strip();assert commit
  git('merge-base','--is-ancestor',commit,'origin/master');tree=git('ls-tree',commit,'--',name).decode().strip();mode,kind,rest=tree.split(' ',2);blob,path=rest.split('\t');assert kind=='blob' and path==name
  raw=git('show',commit+':'+name);assert len(raw)<=1048576 and hashlib.sha256(raw).hexdigest()==link['sha256'];assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob
  assert hashlib.sha256(Path(doc['source_path']).read_bytes()).hexdigest()==doc['source_sha256']
  rows.append({'source_document':doc['source_path'],'document_sha256':doc['source_sha256'],'document_mentions_seal':False,'manifest':name,'manifest_sha256':link['sha256'],'commit':commit,'git_mode':mode,'git_blob':blob,'manifest_bytes':len(raw),'published_ref':'origin/master','published_ref_commit':anchor,'commit_is_ancestor':True,'repository_blob_matches_seal':True,'independent_external_trust':False,'semantic_review_complete':False,'qualified_for_acceptance':False})
 e=Path('research/evidence/canvas-anchor-reconciliation-2026-10-14');e.mkdir();atomic(e/'anchors.json',{'rows':rows,'source_crosswalk_manifest_sha256':prior['manifest_sha256'],'scope':'Repository snapshot anchoring only; does not add a missing seal to the original report or certify evidence semantics/independent trust.','task_accepted':False,'handoff_approved':False})
 atomic(e/'manifest.json',{'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}})
 c={'status':'repository-anchors-captured-semantic-review-pending','evidence':str(e),'manifest_sha256':hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),'created_at':now(),'anchors':2,'next_wake_hint':'Two report-missing seal references now have repository commit/blob anchors. Source reports still omit digests; independent external trust and semantic review remain unqualified. Stop repeating seal/ancestry scans; advance separate-context review or collect genuinely missing provenance evidence.'};d['canvas_anchor_reconciliation_checkpoint']=c;atomic(Path('research/loop/continuous.json'),d);Path('/private/tmp/anchor-checkpoint.json').write_text(json.dumps(c));print([(r['manifest'],r['commit'],r['manifest_sha256']) for r in rows])
