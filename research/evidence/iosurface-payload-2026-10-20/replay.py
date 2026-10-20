"""Rebuild/run owned IOSurface receiver boundary; never targets Xcode."""
from pathlib import Path
import subprocess,sys,json
root=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
source=Path(__file__).resolve().parent;w=Path(sys.argv[1]).resolve();w.mkdir(parents=True,exist_ok=False)
pixels=bytes([0,0,255,255,0,128,0,128,64,0,0,64,0,0,0,0,12,20,30,80,255,255,255,255])
expected=pixels[:12]+bytes([0xd3])*52+pixels[12:]+bytes([0xd4])*52
rgba=bytearray([0xcd]*56)
for y in range(2):
 for x in range(3):
  p=pixels[(y*3+x)*4:(y*3+x+1)*4];rgba[y*20+x*4:y*20+x*4+4]=bytes([p[2],p[1],p[0],p[3]])
def verify(s,b):assert s==expected and b==rgba
with Controller().lock():
 clang='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
 p=subprocess.run([clang,'-Wall','-Wextra','-Werror',str(source/'oracle.m'),'-framework','Foundation','-framework','IOSurface','-framework','CoreGraphics','-o',str(w/'oracle')],capture_output=True,timeout=30);(w/'build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
 p=subprocess.run([str(w/'oracle'),str(w)],capture_output=True,timeout=15);(w/'native.log').write_bytes(p.stdout+p.stderr);p.check_returncode();native=json.loads(p.stdout)
 verify((w/'snapshot.bin').read_bytes(),(w/'output.rgba').read_bytes())
 assert (w/'generation2.bin').read_bytes()==bytes([0x19])*128
 assert native['same_surface_id_new_contents'] and native['creator_reference_released_before_second_lookup'] and native['prior_snapshot_unchanged']
 assert native['zero_id_returns_nil'] and native['runtime_initializer_signature_verified'] and native['copied_source_mutation_isolated']
 rejected=0
 for s,b in [(expected[:12]+bytes([expected[12]^1])+expected[13:],bytes(rgba)),(expected,bytes(rgba[:-1])+bytes([rgba[-1]^1])),(expected[:-1],bytes(rgba))]:
  try:verify(s,b)
  except AssertionError:rejected+=1
 assert rejected==3
 assert (source/'expected-snapshot.bin').read_bytes()==expected and (source/'expected-output.rgba').read_bytes()==rgba
 result={'native':native,'independent_snapshot_bytes_equal':128,'independent_output_bytes_equal':56,'verifier_mutants_rejected':rejected,'xcode_canvas_transport_observed':False,'final_deallocation_proven':False}
 (w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
