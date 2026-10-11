import pathlib,sys,json,subprocess,os,importlib.util
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('ownedcache',sys.argv[1]);cache=importlib.util.module_from_spec(spec);spec.loader.exec_module(cache)
from reloop.primarysource import expression
out=pathlib.Path(sys.argv[2]);out.mkdir();kind=sys.argv[3];clang=out/'clang';ld=out/'ld';clang.write_bytes(b'owned fixture compiler');ld.write_bytes(b'owned fixture linker');calls=[]
def compiler(args,**kw):
 calls.append([str(x) for x in args]);p=pathlib.Path(args[args.index('-o')+1]);p.write_text("; ModuleID = 'owned'\nsource_filename = \"owned\"\nowned IR\n") if '-emit-llvm' in args else p.write_bytes(b'\0asm\x01\0\0\0owned module');return subprocess.CompletedProcess(args,0,b'',b'')
with patch.object(cache.subprocess,'run',side_effect=compiler):
 a=cache.build(expression(4),out/'cache',out/'output',clang,ld);b=cache.build(expression(4),out/'cache',out/'output',clang,ld);assert b['cache_hit'] and len(calls)==2
 pointer=(out/'output/current.json').read_bytes();module=(out/'output'/a['module']).read_bytes();bad=out/'cache'/('keys/'+a['cache_key']+'.json' if kind=='index' else 'entries/'+a['entry_sha256']+'/manifest.json');bad.unlink();os.mkfifo(bad)
 (out/'before.json').write_text(json.dumps({'kind':kind,'receipt':a,'calls':calls,'pointer_hex':pointer.hex(),'module_hex':module.hex(),'bad_path':str(bad)},indent=2)+'\n');print('entered',flush=True)
 try:cache.build(expression(4),out/'cache',out/'output',clang,ld)
 except Exception as ex:
  (out/'after.json').write_text(json.dumps({'error_type':type(ex).__name__,'error':str(ex),'calls':calls,'pointer_hex':(out/'output/current.json').read_bytes().hex(),'module_hex':(out/'output'/a['module']).read_bytes().hex()},indent=2)+'\n');print('rejected',flush=True)
 else:raise AssertionError('FIFO admitted')
