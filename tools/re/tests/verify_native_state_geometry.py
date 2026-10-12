import hashlib,json,re
from pathlib import Path
PHASES=['initial','repeat','changed-immediate','changed-drained','compact-content','compact-repeat','held-false','held-true','original-content','changed-id','old-binding-after-reset']
COLORS=['red','red','blue','blue','blue','blue','red','blue','blue','red','red']
SIZES=[[17,9]]*4+[[11,5]]*4+[[17,9]]*3
BLUE={2,3,4,5,7,8}
def expected(color,width,height):
 raw=bytearray([0xc3])*16384;pixel=bytes({'red':[255,0,0,255],'blue':[0,0,255,255],'green':[0,255,0,255],'yellow':[255,255,0,255]}[color])
 for y in range(height):raw[y*80:y*80+width*4]=pixel*width;raw[y*80+width*4:y*80+80]=bytes([0xa5])*(80-width*4)
 return bytes(raw)
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 compile=json.loads((e/'compile.json').read_text());assert compile['code']==0 and compile['timeout'] is False and compile['stdout']==compile['stderr']=='';total=0;images=[]
 for index in range(2):
  root=e/('run-'+str(index));wait=json.loads((root/'wait.json').read_text());assert wait['code']==0 and wait['timeout'] is False and wait['stdout']=='' and re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} state-geometry\[\d+:\d+\] ApplePersistence=NO\n',wait['stderr'])
  d=json.loads((root/'result.json').read_text());assert d['owned_windows']==0
  assert d['actions']==[{'action':'set-true','before':False,'after':True},{'action':'held-false','before':True,'after':False},{'action':'held-true','before':False,'after':True},{'action':'old-held-false','before':True,'after':False}]
  rows=d['rows'];assert [z['phase'] for z in rows]==PHASES;assert len({z['renderer_identity'] for z in rows})==1 and len({z['probe_identity'] for z in rows})==1
  current=[]
  for i,row in enumerate(rows):
   assert row['binding_present'] is True and row['captures']==[1,1,2,2,3,3,4,5,6,7,7][i]
   assert row['last_body_blue'] is (i in BLUE) and row['last_captured_getter'] is (i in BLUE)
   assert row['root_token']==row['last_token']==(1 if i in [9,10] else 0)
   assert row['compact'] is (i in [4,5,6,7]) and row['last_compact'] is (i in [4,5,6,7])
   assert row['callbacks']==1 and row['size']==SIZES[i] and row['width']==SIZES[i][0] and row['height']==SIZES[i][1] and row['stride']==80 and row['allocation_bytes']==16384 and row['bitmap_info']==16385 and row['alpha_info']==1 and row['bits_per_component']==8 and row['bits_per_pixel']==32 and row['color_space']=='kCGColorSpaceSRGB'
   raw=(root/(row['phase']+'.raw')).read_bytes();assert raw==expected(COLORS[i],*SIZES[i]);total+=len(raw);current.append(raw)
  images.append(current)
 assert images[0]==images[1] and total==360448
 pred=json.loads((e/'prediction.json').read_text());assert pred['expected_sizes']==SIZES and pred['expected_colors']==COLORS and pred['budgets']=={'producer_slots':4,'compile_seconds':60,'native_seconds':15,'native_alarm_seconds':12,'native_repeats':2}
 a=json.loads((e/'assessment.json').read_text());assert a=={'public_state_geometry_qualified': True, 'native_ui_input_qualified': False, 'canvas_refresh_qualified': False, 'general_state_migration_qualified': False, 'prediction_supported': True, 'native_producers': 2, 'compile_producers': 1, 'controlled_bytes': 360448, 'padding_bytes': 2952, 'unused_tail_bytes': 347168}
 env=json.loads((e/'environment.json').read_text());assert env['compiler_sha256']=='2ed38571e92c0283091838c1649e27650ad9c99950288e883c7b2dc6c4ce89fb' and env['helper_sha256']=='e5a78252a9fca0a0e852d51b5923db0bd3b9ad2c26432244fd91474e60fc2a51' and env['sdk'].endswith('MacOSX26.5.sdk')
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0' and rea['target']['architecture']=='arm64' and rea['target']['sha256']==env['helper_sha256']
 return {'native_runs':2,'allocations':22,'controlled_bytes':total,'padding_bytes':2952,'unused_tail_bytes':347168,'owned_state_geometry_qualified':True,'native_ui_input_qualified':False,'canvas_reset_qualified':False}
