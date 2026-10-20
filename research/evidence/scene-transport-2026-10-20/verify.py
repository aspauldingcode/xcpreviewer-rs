from pathlib import Path
import json,hashlib,sys,tempfile,shutil
TEXT='78b6a9d4ec80f7ce56ee2345ca57b185a418320dd48fc9c1a50fff62dbaceda7'
PROBES=['889cfb1518ec55e56127430ffa2315efe91c1b51fefe5d06bbec1ee1c0a82fc2','73b70482c83a160e4ca33d6670ec220cb56855bcec80ebde4f5da3f327961f2b']
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(folder):
 m=json.loads((folder/'mapped.json').read_text());assert m['uuid']=='b66e691cf2d13a7294ed78d92a28c252'
 text=(folder/'segment-00.bin').read_bytes();assert len(text)==1047872 and sha(text)==TEXT
 for i,s in enumerate(m['symbols']):
  assert len(m['symbols'])==2;data=(folder/('symbol-%d.bin'%i)).read_bytes();assert len(data)==32 and sha(data)==PROBES[i]
  offset=int(s['address'],16)-int(m['segments'][0]['address'],16);assert offset>=0 and text[offset:offset+32]==data
 bindings=json.loads((folder/'bindings.stdout').read_text());assert len(bindings)==2 and all(x['exact_match'] is True for x in bindings)
 assert [x['exact_dlsym_symbol'] for x in bindings]==['$s18PreviewsServicesUI14SceneMessengerC13receiveActionyySo8BSActionCF','$s18PreviewsServicesUI20UVPreviewSceneActionCMa']
 sel=json.loads((folder/'selectors.stdout').read_text());assert sel['uuid']==m['uuid'] and {x['name'] for x in sel['selectors']}=={'sendActions:','scene:didReceiveActions:','scene:handleActions:'}
 inventory=json.loads((folder/'shell.stdout').read_text());rows=[row for rows in inventory.values() for row in rows if row['selector']=='scene:didReceiveActions:'];assert len(rows)==1 and rows[0]['types']=='v32@0:8@16@24' and rows[0]['address']==m['symbols'][1]['address']
if __name__=='__main__':
 f=Path(sys.argv[1]);verify(f);rejected=0
 with tempfile.TemporaryDirectory() as d:
  d=Path(d)
  for name in ['mapped.json','segment-00.bin','symbol-0.bin','symbol-1.bin','bindings.stdout','selectors.stdout','shell.stdout']:shutil.copyfile(f/name,d/name)
  changes=[('segment-00.bin',lambda b:b[:-1]+bytes([b[-1]^1])),('symbol-0.bin',lambda b:bytes([b[0]^1])+b[1:]),('mapped.json',lambda b:b.replace(b'b66e691cf2d13a7294ed78d92a28c252',b'00000000000000000000000000000000')),('bindings.stdout',lambda b:b.replace(b'true',b'false',1)),('shell.stdout',lambda b:b.replace(b'v32@0:8@16@24',b'v32@0:8Q16@24'))]
  for name,change in changes:
   p=d/name;original=p.read_bytes();p.write_bytes(change(original))
   try:verify(d)
   except (AssertionError,ValueError,KeyError):rejected+=1
   p.write_bytes(original)
 assert rejected==5
 print(json.dumps({'native_executable_bytes_equal':1047872,'native_probe_bytes_equal':64,'exact_import_bindings':2,'corruption_controls_rejected':5,'live_canvas_transport_observed':False}))
