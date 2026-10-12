import hashlib,json,re
from pathlib import Path
PHASES=['initial','repeat','changed-immediate','changed-drained','fresh-same-content','original-after-fresh','fresh-default-root','reset-immediate','reset-drained']
BLUE={2,3,5}
def expected(blue):
 raw=bytearray([0xc3])*16384;pixel=bytes([0,0,255,255] if blue else [255,0,0,255])
 for y in range(9):raw[y*80:y*80+68]=pixel*17;raw[y*80+68:y*80+80]=bytes([0xa5])*12
 return bytes(raw)
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 compile=json.loads((e/'compile.json').read_text());assert compile['code']==0 and compile['timeout'] is False and compile['stdout']==compile['stderr']=='';total=0;images=[]
 for index in range(2):
  root=e/('run-'+str(index));wait=json.loads((root/'wait.json').read_text());assert wait['code']==0 and wait['timeout'] is False and wait['stdout']=='' and re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} state-binding\[\d+:\d+\] ApplePersistence=NO\n',wait['stderr'])
  d=json.loads((root/'result.json').read_text());assert d['owned_windows']==0 and d['actions']==[{'action':'set-true','before':False,'after':True},{'action':'set-false','before':True,'after':False}];rows=d['rows'];assert [r['phase'] for r in rows]==PHASES;original=rows[0]['renderer_identity'];fresh=rows[4]['renderer_identity'];reset=rows[6]['renderer_identity'];assert len({original,fresh,reset})==3;probe=rows[0]['probe_identity'];replacement=rows[6]['probe_identity'];assert probe!=replacement
  current=[]
  for i,row in enumerate(rows):
   assert row['renderer_identity']==(fresh if i==4 else reset if i==6 else original) and row['probe_identity']==(replacement if i==6 else probe) and row['binding_present'] is True and row['captures']==[1,1,2,2,3,3,1,4,4][i] and row['last_body_blue'] is (i in [2,3]) and row['last_captured_getter'] is (i in [2,3])
   assert row['callbacks']==1 and row['size']==[17,9] and row['width']==17 and row['height']==9 and row['stride']==80 and row['allocation_bytes']==16384 and row['bitmap_info']==16385 and row['alpha_info']==1 and row['bits_per_component']==8 and row['bits_per_pixel']==32 and row['color_space']=='kCGColorSpaceSRGB'
   raw=(root/(row['phase']+'.raw')).read_bytes();assert raw==expected(i in BLUE);total+=len(raw);current.append(raw)
  images.append(current)
 assert images[0]==images[1] and total==294912
 pred=json.loads((e/'prediction.json').read_text());assert pred['retained_state_expected_colors']==['blue' if i in BLUE else 'red' for i in range(9)] and pred['budgets']=={'producer_slots':4,'compile_seconds':60,'native_seconds':15,'native_alarm_seconds':12,'native_repeats':2}
 a=json.loads((e/'assessment.json').read_text());assert a['public_binding_state_control_qualified'] is True and a['native_ui_input_qualified'] is False and a['canvas_refresh_qualified'] is False and a['general_state_migration_qualified'] is False and a['retained_state_prediction_supported'] is True and a['native_producers']==2 and a['compile_producers']==1 and a['controlled_bytes']==294912 and a['padding_bytes']==1944 and a['unused_tail_bytes']==281952
 env=json.loads((e/'environment.json').read_text());assert env['compiler_sha256']=='2ed38571e92c0283091838c1649e27650ad9c99950288e883c7b2dc6c4ce89fb' and env['helper_sha256']=='eaa9f4561f485942cdbe81d58c124e121d76ccb050f557fa8ed1ed9393c42c38' and env['sdk'].endswith('MacOSX26.5.sdk')
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0' and rea['target']['architecture']=='arm64' and rea['target']['sha256']==env['helper_sha256']
 return {'native_runs':2,'allocations':18,'controlled_bytes':total,'padding_bytes':1944,'unused_tail_bytes':281952,'owned_state_binding_qualified':True,'native_ui_input_qualified':False,'canvas_reset_qualified':False}
