"""Owned persistent AppKit host; actual native pointer events, no global input injection."""
from pathlib import Path
import json,os,select,shutil,signal,subprocess,threading,time,secrets

class NativeHost:
    def __init__(self,executable,work,width,height,scale):
        self.identity=secrets.token_hex(16);self.work=Path(work);self.work.mkdir(parents=True,exist_ok=True)
        self.stderr=(self.work/'stderr.log').open('wb');self.lock=threading.Lock();self.sequence=0;self.buffer=b'';self.logs=[];self.closed=False
        try:
            self.process=subprocess.Popen([str(executable),str(width),str(height),str(scale),str(self.work)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,start_new_session=True,env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')})
        except BaseException:
            self.stderr.close();raise
        os.set_blocking(self.process.stdout.fileno(),False)
        self.width,self.height,self.scale=width,height,scale
    def request(self,action,**values):
        with self.lock:
            if self.closed:raise RuntimeError('Native view closed')
            self.sequence+=1;identifier=self.sequence
            self.process.stdin.write(json.dumps(dict(id=identifier,action=action,**values)).encode()+b'\n');self.process.stdin.flush()
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                while b'\n' in self.buffer:
                    line,self.buffer=self.buffer.split(b'\n',1)
                    if not line.startswith(b'XCPVJSON:'):
                        self.logs.append(line.decode(errors='replace'));self.logs=self.logs[-64:];continue
                    value=json.loads(line[9:])
                    if value.get('id')!=identifier:raise RuntimeError('Native response sequence mismatch')
                    if not value.get('ok'):raise RuntimeError(value.get('error','Native input failed'))
                    return value,(self.work/'frame.bplist').read_bytes()
                readable,_,_=select.select([self.process.stdout],[],[],max(0,deadline-time.monotonic()))
                if readable:
                    data=os.read(self.process.stdout.fileno(),65536)
                    if not data:raise RuntimeError('Native view exited: '+(self.work/'stderr.log').read_text(errors='replace')[-2000:])
                    self.buffer+=data
                    if len(self.buffer)>1024*1024:raise RuntimeError('Native response exceeds limit')
            raise RuntimeError('Native input exceeded 8 seconds')
    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True
            if self.process.poll() is None:
                self.process.stdin.close()
                try:self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(self.process.pid,signal.SIGKILL);self.process.wait(timeout=3)
            self.process.stdout.close();self.stderr.close()
        shutil.rmtree(self.work,ignore_errors=True)
