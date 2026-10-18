import sys,json,datetime,hashlib,select,time
from pathlib import Path
sys.path.insert(0,'/Users/8amps/xcpreviewer-rs/tools/re')
from reloop.core import Controller,atomic
from reloop.xcodebridge import BrokerClient,manage
r=Path('/Users/8amps/xcpreviewer-rs');p=Path('/private/tmp/callback-ui-access-20261018');source=p/'workspace/Sources/PreviewLab/PreviewLab.swift'
with Controller().lock():
 cp=r/'research/loop/continuous.json';v=json.loads(cp.read_text());record=v['canvas_callback_ui_access_checkpoint']
 if record['status']!='cleanup_unverified_blocks_further_controller_work':raise ValueError('Unexpected checkpoint')
 if hashlib.sha256(source.read_bytes()).hexdigest()!=record['source_sha256']:raise ValueError('Source changed')
 before=BrokerClient(timeout=8).request('tools/call',{'name':'XcodeListWindows','arguments':{}})
 (p/'reconciliation-before.json').write_text(json.dumps(before,indent=2)+'\n')
 print(json.dumps({'cleanup_only':True,'before':before}),flush=True)
 ready,_,_=select.select([sys.stdin],[],[],90)
 if not ready or json.loads(sys.stdin.readline())!={'op':'finish'}:raise ValueError('Cleanup remains unverified')
 after=BrokerClient(timeout=8).request('tools/call',{'name':'XcodeListWindows','arguments':{}})
 data=after.get('structuredContent') or json.loads(after['content'][0]['text'])
 if after.get('isError',False) or data.get('message')!='No workspace windows found':raise ValueError('Not zero windows')
 if hashlib.sha256(source.read_bytes()).hexdigest()!=record['source_sha256']:raise ValueError('Source changed')
 result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'windows':after,'owned_workspace_windows':0,'source_sha256':record['source_sha256'],'original_deadline_missed':True,'experiment_reopened':False}
 (p/'reconciliation-cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
 record.update(status='late_cleanup_verified_experiment_failed_review_pending',cleanup_reconciliation_required=False,reconciled_at=result['at'],experiment_deadline_closed=True)
 atomic(cp,v);print(json.dumps({'cleanup_verified':True}),flush=True)
