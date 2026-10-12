import os,sys,time,json,pathlib,ctypes
folder=pathlib.Path(sys.argv[1]);mode=sys.argv[2];child=None
if mode=='detached':
 readfd,writefd=os.pipe();child=os.fork()
 if child==0:
  os.close(readfd);parent=os.getppid();os.setsid()
  with (folder/'heartbeat.bin').open('wb',buffering=0) as out:
   for i in range(32):
    out.write(bytes([i]))
    if i==0:os.write(writefd,b'1');os.close(writefd)
    time.sleep(0.05)
  (folder/'child-finished.json').write_text(json.dumps({'pid':os.getpid(),'original_parent':parent,'group':os.getpgrp(),'bytes':32,'self_terminated':True})+'\n');os._exit(0)
 os.close(writefd);assert os.read(readfd,1)==b'1';os.close(readfd)
system=ctypes.CDLL('/usr/lib/libSystem.B.dylib');f=system._NSGetExecutablePath;f.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)];f.restype=ctypes.c_int;n=ctypes.c_uint32(4096);b=ctypes.create_string_buffer(n.value);assert f(b,ctypes.byref(n))==0
row={'pid':os.getpid(),'parent':os.getppid(),'group':os.getpgrp(),'child_pid':child,'executable':str(pathlib.Path(os.fsdecode(b.value)).resolve())};tmp=folder/'ready.tmp';tmp.write_text(json.dumps(row)+'\n');os.replace(tmp,folder/'ready.json');time.sleep(0.45)
print('owned observed root' if mode=='clean' else json.dumps(row),flush=True)
