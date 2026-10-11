import os,sys,signal,resource,json,pathlib
signal.signal(signal.SIGXFSZ,signal.SIG_DFL)
pathlib.Path(sys.argv[2]).write_text(json.dumps({'file_limit':list(resource.getrlimit(resource.RLIMIT_FSIZE))}))
fd=1 if sys.argv[1]=='stdout' else 2
remaining=b'Z'*8192
while remaining:remaining=remaining[os.write(fd,remaining):]
