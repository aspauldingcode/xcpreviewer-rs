import pathlib,sys,json,os,selectors,subprocess,time,shutil

def run(runtime,preloader,out,fixed):
 runtime=pathlib.Path(runtime).resolve();out=pathlib.Path(out).resolve();out.mkdir();records=[]
 for mode in ['complete','hung']:
  root=out/mode;root.mkdir();source=root/'owned.swift';source.write_text('owned shutdown watchdog');config=root/'config.json';config.write_text(json.dumps({k:'owned test fixture; not invoked' for k in ['cli','observer','python','rustc','rustcSha','toolchainPin']}));packets=[];buffer=bytearray();timed_out=False
  with (root/'stderr.txt').open('wb') as stderr:
   p=subprocess.Popen([shutil.which('node'),'--require',str(pathlib.Path(preloader).resolve()),str(runtime/'tools/re/preview_mcp_stdio.js'),str(config),str(source),str(root/'builds'),'500'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,env=dict(os.environ,OWNED_CLEANUP_MODE=mode));pid=p.pid
   def send(m):p.stdin.write((json.dumps(m)+'\n').encode());p.stdin.flush()
   def read():
    deadline=time.monotonic()+3
    with selectors.DefaultSelector() as selector:
     selector.register(p.stdout,selectors.EVENT_READ)
     while b'\n' not in buffer:
      assert selector.select(max(0,deadline-time.monotonic())),'Response deadline';b=os.read(p.stdout.fileno(),4096);assert b;buffer.extend(b);assert len(buffer)<=32768
    line,_,rest=buffer.partition(b'\n');buffer[:]=rest;row=json.loads(line);packets.append(row);return row
   try:
    send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'owned-watchdog','version':'1'}}});assert read()['result']['protocolVersion']=='2025-11-25';send({'jsonrpc':'2.0','method':'notifications/initialized'})
    for ident,name in [(2,'start'),(3,'frame')]:
     send({'jsonrpc':'2.0','id':ident,'method':'tools/call','params':{'name':'preview_'+name,'arguments':{}}});row=read();assert not row['result'].get('isError')
    p.stdin.close()
    try:code=p.wait(timeout=5)
    except subprocess.TimeoutExpired:timed_out=True;p.kill();code=p.wait(timeout=2)
    assert not p.stdout.read(32769) and not buffer
    expected=(4 if fixed else -9) if mode=='hung' else 0;assert code==expected,(code,expected);assert timed_out==(mode=='hung' and not fixed)
    normal=root/'builds/session-lifecycle.json';watchdog=root/'builds/shutdown-timeout.json';artifact=json.loads((watchdog if fixed and mode=='hung' else normal).read_text()) if mode=='complete' or fixed else None
    if mode=='complete':assert artifact['channel']['cleanup']=='complete' and artifact['final']['lifecycle']['liveWorkers']==0
    elif fixed:assert artifact['kind']=='shutdown-timeout' and artifact['final']['lifecycle']['liveWorkers']==1 and not normal.exists()
    else:assert not normal.exists() and not watchdog.exists()
    records.append({'mode':mode,'pid':pid,'code':code,'wait_timeout':timed_out,'process_reaped':p.poll() is not None,'packets':packets,'artifact':artifact})
   finally:
    if not p.stdin.closed:p.stdin.close()
    if p.poll() is None:p.kill();p.wait(timeout=2)
    p.stdout.close()
 (out/'result.json').write_text(json.dumps({'fixed':fixed,'records':records},indent=2)+'\n')
if __name__=='__main__':run(*sys.argv[1:4],sys.argv[4]=='fixed')
