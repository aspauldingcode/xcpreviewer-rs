import pathlib,sys,json,subprocess,os

def run(cli,out,fixed):
 out=pathlib.Path(out);out.mkdir();records=[]
 for kind in ['fifo','symlink']:
  root=out/kind;root.mkdir();source=root/'owned.swift'
  if kind=='fifo':os.mkfifo(source)
  else:
   target=root/'target.swift';target.write_bytes(b'Text("owned unsupported")');source.symlink_to(target)
  args=[sys.executable,str(cli),str(source),'--cache',str(root/'cache'),'--output',str(root/'output'),'--clang',str(root/'missing-clang'),'--wasm-ld',str(root/'missing-linker')]
  p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,PYTHONPATH=str(pathlib.Path(__file__).resolve().parents[3]/'tools/re')));pid=p.pid
  try:
   try:stdout,stderr=p.communicate(timeout=1.5);timedout=False
   except subprocess.TimeoutExpired:p.kill();stdout,stderr=p.communicate(timeout=2);timedout=True
   records.append({'kind':kind,'pid':pid,'wait':{'code':p.returncode,'timeout':timedout,'reaped':p.poll() is not None},'stdout':stdout.decode(),'stderr':stderr.decode(),'cache_created':(root/'cache').exists(),'output_created':(root/'output').exists()})
  finally:
   if p.poll() is None:p.kill();p.wait(timeout=2)
   p.stdout.close();p.stderr.close();source.unlink()
 (out/'result.json').write_text(json.dumps({'fixed':fixed,'records':records},indent=2)+'\n')
if __name__=='__main__':run(sys.argv[1],sys.argv[2],sys.argv[3]=='fixed')
