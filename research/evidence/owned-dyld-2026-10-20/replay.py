"""Replay the owned public-API injection boundary, never targeting Xcode.

Run with: python3 replay.py /private/tmp/FRESH-OUTPUT
Acquires the repository controller lock. Only newly launched children are killed
on a deadline. Requires existing Apple clang and public SDK frameworks.
"""
from pathlib import Path
import subprocess,os,json,sys,hashlib,shutil
source=Path(__file__).resolve().parent
root=Path('/Users/8amps/xcpreviewer-rs')
w=Path(sys.argv[1]).resolve();w.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
clang='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
def run(args,env=None):
 p=subprocess.Popen(list(map(str,args)),env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:out,err=p.communicate(timeout=30)
 except subprocess.TimeoutExpired:
  p.kill();out,err=p.communicate(timeout=5)
  raise RuntimeError('Owned child exceeded deadline; killed child only, settlement beyond the synchronous probe is unqualified')
 if p.returncode:raise RuntimeError(str(args)+' '+err.decode())
 return p.pid,out,err

def verify(trace,pid,retained=False,failure=False):
 rows=[line.split() for line in trace.splitlines()]
 assert rows and all(len(r)==3 and r[0]==str(pid) for r in rows)
 kinds=[r[1] for r in rows]
 if failure:
  assert kinds==['loaded','create-enter','create-return'] and rows[-1][2]=='0x0'
 else:
  expected=['loaded','create-enter','create-return']
  if retained:expected+=['retain-enter','retain-return','release-enter','release-return']
  expected+=['release-enter','release-return']
  assert kinds==expected
  handle=rows[2][2];assert handle!='0x0'
  assert all(r[2]==handle for r in rows[3:])
 return kinds

with Controller().lock():
 run([clang,'-Wall','-Wextra','-Werror','-dynamiclib',source/'observe.c','-framework','CoreGraphics','-o',w/'observe.dylib'])
 for name in ['oracle','failure']:run([clang,'-Wall','-Wextra','-Werror',source/(name+'.c'),'-framework','CoreGraphics','-framework','CoreFoundation','-o',w/name])
 retained_source=(source/'oracle.c').read_text().replace('CGContextRelease(context);','CGImageRetain(image);CGImageRelease(image);CGContextRelease(context);')
 assert retained_source!=(source/'oracle.c').read_text()
 (w/'retained.c').write_text(retained_source)
 run([clang,'-Wall','-Wextra','-Werror',w/'retained.c','-framework','CoreGraphics','-framework','CoreFoundation','-o',w/'retained'])
 results=[]
 for flags in ['2002','4002','2001','4001']:
  trace=w/(flags+'.trace')
  base=os.environ.copy();base.pop('DYLD_INSERT_LIBRARIES',None);base.pop('DYLD_PRINT_LIBRARIES',None);base['OWNED_CG_TRACE']=str(trace)
  inp=source/(flags+'.bin')
  run([w/'oracle',str(int(flags,16)),inp,w/(flags+'-plain.rgba'),w/(flags+'-plain.json')],base)
  assert not trace.exists(),'Negative control unexpectedly loaded interposer'
  env=base.copy();env['DYLD_INSERT_LIBRARIES']=str(w/'observe.dylib');env['DYLD_PRINT_LIBRARIES']='1'
  pid,_,err=run([w/'oracle',str(int(flags,16)),inp,w/(flags+'-hooked.rgba'),w/(flags+'-hooked.json')],env)
  (w/(flags+'-dyld.log')).write_bytes(err)
  assert str(w/'observe.dylib') in err.decode()
  kinds=verify(trace.read_text(),pid)
  plain=(w/(flags+'-plain.rgba')).read_bytes();hooked=(w/(flags+'-hooked.rgba')).read_bytes()
  expected=(source/'expected-rgba.bin').read_bytes()
  assert len(plain)==56 and plain==hooked==expected
  results.append({'flags':flags,'events':kinds,'same_created_image_released':True,'all_56_bytes_equal':True,'padding_and_tail_bytes':32,'dyld_independent_library_listing':True,'trace_pid_equals_owned_child':True,'negative_no_trace':True})
 # Changed ownership input: one explicit retain, two explicit releases.
 trace=w/'retained.trace';env=os.environ.copy();env.update(DYLD_INSERT_LIBRARIES=str(w/'observe.dylib'),OWNED_CG_TRACE=str(trace))
 pid,_,_=run([w/'retained',str(0x2002),source/'2002.bin',w/'retained.rgba',w/'retained.json'],env)
 retained_events=verify(trace.read_text(),pid,retained=True)
 assert (w/'retained.rgba').read_bytes()==(source/'expected-rgba.bin').read_bytes()
 results.append({'control':'one explicit retain, two explicit releases','events':retained_events,'all_56_bytes_equal':True,'trace_pid_equals_owned_child':True})
 trace=w/'failure.trace';env['OWNED_CG_TRACE']=str(trace)
 pid,_,_=run([w/'failure'],env)
 kinds=verify(trace.read_text(),pid,failure=True)
 results.append({'failure':'zero-width CGImageCreate returns NULL','events':kinds,'null_return':True,'release_events':0,'synchronous_api_return_observed':True,'trace_pid_equals_owned_child':True})
 # Verifier must reject absence, missing release return, wrong handle and wrong PID.
 valid=(w/'2002.trace').read_text();rows=valid.splitlines();goodpid=int(rows[0].split()[0])
 mutants=['','\n'.join(rows[:-1]),'\n'.join(rows[:-1]+[rows[-1].rsplit(' ',1)[0]+' 0xdeadbeef']),valid.replace(str(goodpid)+' ',str(goodpid+1)+' ',1)]
 rejected=0
 for mutant in mutants:
  try:verify(mutant,goodpid)
  except AssertionError:rejected+=1
 assert rejected==4
 result={'cases':results,'verifier_mutants_rejected':rejected,'private_runtime_invoked':False,'target':'new owned public CoreGraphics hosts only','timeout_alone_proves_settlement':False,'release_call_proves_final_deallocation':False}
 (w/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'cases':len(results),'verifier_mutants_rejected':rejected,'all_pass':True}))
