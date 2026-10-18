import sys,json,hashlib,subprocess,uuid,shutil
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');p=Path('/private/tmp/callback-input-calibration-20261018');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.xcodebridge import BrokerClient,manage
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
with Controller().lock():
 cp=json.loads((r/'research/loop/continuous.json').read_text());prior=cp['canvas_input_calibration_checkpoint']
 if prior['cleanup_reconciliation_required'] or prior['status']!='sealed_scoped_owned_preview_publication_verified':raise ValueError('Prior cleanup')
 base=r/prior['evidence']
 if sha(base/'seal.json')!=prior['seal_sha256']:raise ValueError('Prior seal')
 subprocess.run([sys.executable,'-B',str(base/'verify-frozen.py')],check=True,capture_output=True,timeout=40)
 status=manage('status')
 if not status['running'] or not status['responsive']:raise ValueError('Bridge lost; no restart')
 windows=BrokerClient(timeout=8).request('tools/call',{'name':'XcodeListWindows','arguments':{}})
 data=windows.get('structuredContent') or json.loads(windows['content'][0]['text'])
 if windows.get('isError',False) or data.get('message')!='No workspace windows found':raise ValueError('Prior windows')
 selection={'prior':prior,'bridge':status,'windows':windows,'graph_basis':'sealed planner-stage-profile-2026-10-18; no graph execution/new legacy wake; unchanged expensive full inspection skipped','runner_sha256':sha(r/'research/loop/graph-runner.json'),'workgraph_sha256':sha(r/'research/loop/workgraph.json')}
 for k,a in {'backlog':['gh','issue','list','--repo','aspauldingcode/xcpreviewer-rs','--state','open','--json','number,title,milestone','--limit','100'],'validate':['python3','tools/re/canvas_graph.py','validate'],'canvas_plan':['python3','tools/re/canvas_graph.py','plan']}.items():
  x=subprocess.run(a,cwd=r,capture_output=True,text=True,timeout=30);selection[k]={'returncode':x.returncode,'stdout':x.stdout,'stderr':x.stderr}
 (p/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
 workspace=Path(prior['workspace']);source=workspace.parent/'Sources/PreviewLab/PreviewLab.swift'
 if sha(source)!=prior['source_sha256']:raise ValueError('Fixture source changed')
 nonce=uuid.uuid4().hex;old='20d74faa8f664eca9618ae35ac7b3141';newsource=source.read_text().replace(old,nonce)
 (p/'fixture-before.swift').write_bytes(source.read_bytes());source.write_text(newsource);(p/'fixture-source.swift').write_bytes(source.read_bytes())
 root=Path('/private/tmp/xcpreviewer-callback-'+nonce);root.mkdir(mode=0o700);(root/'receipts').mkdir(mode=0o700)
 binding={'projects':[],'sources':[],'filesystem':{}}
 for k,path in [('projects',workspace),('sources',source)]:
  alias=Path(str(path).replace('/private/tmp/','/tmp/',1))
  if not path.samefile(alias):raise ValueError('Alias mismatch')
  binding[k]=[str(path),str(alias)];a=path.stat();b=alias.stat();binding['filesystem'][k]={'requested_stat':[a.st_dev,a.st_ino],'observed_stat':[b.st_dev,b.st_ino],'canonical':str(path.resolve())}
 (p/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
 plan={'scope':'One owned conditional screenshot-coordinate calibration and repeated native input control','workspace':str(workspace),'source_sha256':sha(source),'nonce':nonce,'receipt_root':str(root/'receipts'),'stop_new_actions_utc':'2026-10-18T22:28:00Z','deadline_utc':'2026-10-18T22:29:00Z','maximum_workspace_opens':1,'maximum_refresh_clicks':1,'maximum_preview_selection_clicks':1,'maximum_increment_clicks':2,'maximum_renderpreview_calls':0,'maximum_state_observations':24,'maximum_passive_readiness_observations':4,'maximum_receipt_observations':3,'method':'Exclusivelease verifieszero/source/pins. Open exactfixture; quickopensource ifneeded. Use16assertiontestednewguard; twoexactnonbusy signatures and samecallownership/signature/cutoff before<=1Refresh+<=1Textandinteractionselection. Stoponerrors/ambiguity; <=2coordinate Increment candidatesonlyafterfreshscreenshotgeometrycontainment underdeclaredfactor1/factor2 and baselineappear0receiptverified. Firstcandidatepoint halfbuttoncenter; factor1 landsinsideownedSourceEditor andfactor2insidebutton. Ifexactincrement1notobserved,stopwithoutsecondclick. SecondclickonlyafterfreshsameUUID Count1screenshot/buttongeometry+receipt/livePIDvalidate. <=3boundedreceiptreads<=4files+publiclibprocidentity; exactappear0/increment1/increment2transcripts required. Noothercoordinates/privatecapture/settingschanges, thenexactownedclose+brokerzero/sourcecheck. Freshnonce/path; allpriorplansclosed.','limitations':'Actualbytes plus verifiedownedliveexecutableidentity required for callbackaccess claim; no source strings/operatorobservations alone. No continuousprocess/privatewire/state/input acceptance.'}
 (p/'experiment.json').write_text(json.dumps(plan,indent=2)+'\n')
 lease=Path('/private/tmp/callback-ui-access-20261018/lease.py').read_text().replace('canvas_callback_ui_access_checkpoint','canvas_input_calibration_checkpoint')
 lease=lease.replace('receipt_observations>=1','receipt_observations>=3').replace('len(entries)>2','len(entries)>4').replace("p/'receipt-observation.json'","p/('receipt-observation-%d.json'%receipt_observations)")
 (p/'lease.py').write_text(lease)
 shutil.copy2('/private/tmp/canvas-preview-selection-20261018/prior-final-projection.ax.txt',p/'prior-final-projection.ax.txt')
 f=p/'test-guard.mjs';f.write_text(f.read_text().replace("'/private/tmp/canvas-preview-selection-20261018/prior-final-projection.ax.txt'","new URL('./prior-final-projection.ax.txt',import.meta.url)"))
 pins={n:sha(p/n) for n in ['lease.py','experiment.json','binding.json','guard.mjs','fixture-source.swift','geometry.py']}
 for f in [source,workspace/'project.pbxproj',r/'research/build/libproc-observer/owned-process-snapshot']:pins[str(f)]=sha(f)
 (p/'approved-pins.json').write_text(json.dumps(pins,indent=2)+'\n');print(json.dumps(plan))
