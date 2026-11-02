"""Small MCP stdio client for local Ghidra bridges (JSON lines or LSP framing)."""
import json
import queue
import subprocess
import threading
import time


class Client:
    def __init__(self,command,stderr,timeout=15,env=None,observer=None):
        self.timeout=timeout;self.counter=0;self.messages=queue.Queue();self.observer=observer
        self.process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,env=env)
        self.reader=threading.Thread(target=self.read,daemon=True);self.reader.start()
        try:
            self.initialized=self.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'preview-reloop','version':'0.1.0'}})
            self.send({'jsonrpc':'2.0','method':'notifications/initialized'})
        except BaseException:
            self.close()
            raise

    def read(self):
        try:
            while True:
                line=self.process.stdout.readline()
                if not line:break
                if line.lower().startswith(b'content-length:'):
                    size=int(line.split(b':',1)[1]);header=self.process.stdout.readline()
                    while header.strip():header=self.process.stdout.readline()
                    data=self.process.stdout.read(size)
                else:data=line
                message=json.loads(data)
                if self.observer:self.observer('in',message)
                self.messages.put(message)
        except Exception as error:self.messages.put(error)
        finally:self.messages.put(EOFError('MCP bridge closed'))

    def send(self,message):
        if self.observer:self.observer('out',message)
        self.process.stdin.write(json.dumps(message).encode()+b'\n');self.process.stdin.flush()

    def request(self,method,params):
        self.counter+=1;request_id=self.counter
        self.send({'jsonrpc':'2.0','id':request_id,'method':method,'params':params})
        deadline=time.monotonic()+self.timeout
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('MCP request timed out: '+method)
            try:item=self.messages.get(timeout=remaining)
            except queue.Empty:raise TimeoutError('MCP request timed out: '+method) from None
            if isinstance(item,Exception):raise item
            # Server requests occupy an independent ID space, including colliding IDs.
            if 'method' in item and 'id' in item:
                response={'jsonrpc':'2.0','id':item['id']}
                if item['method']=='ping':response['result']={}
                else:response['error']={'code':-32601,'message':'Client method not supported'}
                self.send(response);continue
            if item.get('id')!=request_id:continue
            if 'error' in item:raise RuntimeError(str(item['error']))
            return item['result']

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        self.reader.join(timeout=1)
        self.process.stdin.close();self.process.stdout.close()
