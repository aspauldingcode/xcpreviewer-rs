import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 anchor=json.loads((e/'native-anchor.json').read_text());assert anchor=={'run':'20261010T184640Z-native-primary-layer-holdouts-05e3ae4b','anchor':'0dfae6bf400c8d511bd921027daa9f779d06596ffa177eb3a47cab5d1ae43b28','valid':True,'external_anchor_matches':True}
 cfg={'width':17,'height':9,'alphas':[3,3,8],'reverse':0};build=json.loads((e/'build.json').read_text());cold=build['cold'];hit=build['hit'];assert cold['cache_hit'] is False and hit['cache_hit'] is True and {k:v for k,v in cold.items() if k!='cache_hit'}=={k:v for k,v in hit.items() if k!='cache_hit'} and cold['config']==cfg and len(build['calls'])==2
 for call in build['calls']:assert call['code']==0 and call['timeout'] is False and call['timeout_seconds']==30 and call['preexec_present'] is True and call['start_new_session'] is True and call['group']==call['pid'] and call['stdout']==call['stderr']==''
 assert build['group_checks']==[{'pid':call['pid'],'signal':0,'outcome':'absent'} for call in build['calls']]
 pointer=bytes.fromhex(build['pointer_hex']);assert (e/'output/current.json').read_bytes()==pointer;receipt=json.loads(pointer);assert receipt['module_sha256']==cold['module_sha256']=='1b9601269891f153c9de51d24004dc023682aa32a37935d489ebc7f855b73ab6';module=(e/'output'/receipt['module']).read_bytes();assert hashlib.sha256(module).hexdigest()==receipt['module_sha256'] and module[:8]==b'\0asm\x01\0\0\0'
 published=e/'output'/Path(receipt['module']).parent;manifest=published/'manifest.json';assert hashlib.sha256(manifest.read_bytes()).hexdigest()==cold['entry_sha256'];metadata=json.loads(manifest.read_text());assert metadata['identity']['builder_sha256']==hashlib.sha256((e/'sourcecache.py').read_bytes()).hexdigest() and metadata['cache_key']==cold['cache_key']
 for name,entry in metadata['files'].items():raw=(published/name).read_bytes();assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
 pixel=bytes([60,96,99,255]);native=(pixel*17+bytes([165])*12)*9;assert (e/'native-callback.raw').read_bytes()==native
 def expected(stride):
  prefix=(pixel*17+bytes([165])*(stride-68))*9
  return prefix+bytes([195])*(16384-len(prefix))
 total=0
 for stride_index,stride in enumerate([68,80]):
  for repeat in range(2):
   raw=(e/f'frame-0-{stride_index}-{repeat}.raw').read_bytes();assert raw==expected(stride);total+=len(raw)
 for i in range(4):
  raw=(e/f'invalid-0-{i}.raw').read_bytes();assert raw==expected(68);total+=len(raw)
 execution=json.loads((e/'execution.json').read_text());assert execution['imports']==0 and execution['rows']==[{'job':0,'stride_index':s,'repeat':repeat} for s in range(2) for repeat in range(2)] and execution['invalid']==[{'job':0,'stride':x} for x in [0,67,257,4294967295]]
 for name in ['v8','wasmkit']:
  wait=json.loads((e/(name+'-wait.json')).read_text());assert wait['code']==0 and wait['timeout'] is False and wait['stderr']=='' and wait['stdout']==('' if name=='v8' else '[WasmTypes.Value.i32(720)]\n')
 env=json.loads((e/'environment.json').read_text());assert env['tools']['clang']['sha256']=='71e012199d574fb2d285531d322e4a41a871c3d1ba8a9cadd11ce17d7740d638' and env['tools']['wasmkit']['sha256']=='2ba68ae1418d4bdb9299ad7382385cc4361eaa27abed655c2a21614a9006e957'
 rea=json.loads((e/'rea-status.json').read_text());assert rea['open'] is False and rea['server_identity']['server']['version']=='6.2.0'
 return {'allocation_bytes':total,'native_prefix_bytes':len(native),'wasmkit_result_only':720}
