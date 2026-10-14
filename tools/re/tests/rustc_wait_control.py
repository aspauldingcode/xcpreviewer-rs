import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def run(evidence):
    config = json.loads((evidence/'config.json').read_text())
    rustc = config['rustc']
    helper = config['observer']['helper']
    assert hashlib.sha256(Path(rustc).read_bytes()).hexdigest() == config['rustcSha']
    assert hashlib.sha256(Path(helper).read_bytes()).hexdigest() == config['observer']['sha256']
    for count, mode in enumerate(['cancel-0','cancel-1','success-0','success-1'],1):
        (evidence/'slots.json').write_text(json.dumps({'used':count,'limit':4}))
        root = evidence/mode
        root.mkdir()
        cancelling = mode.startswith('cancel')
        functions = 50000 if cancelling else 1
        source = ''.join('pub fn function_'+str(index)+'()->u64{'+str(index)+'}\n' for index in range(functions))
        (root/'input.rs').write_text(source)
        command = [rustc,'--crate-name','owned_wait','--crate-type','lib','--emit','metadata',str(root/'input.rs'),'-o',str(root/'output.rmeta')]
        started = time.monotonic()
        target = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        observation = None
        repeated = None
        try:
            if cancelling:
                deadline = started+2
                while time.monotonic() < deadline and target.poll() is None:
                    sample = subprocess.run([helper,str(target.pid)],capture_output=True,text=True,timeout=1,check=True)
                    rows = json.loads(sample.stdout)
                    observation = next((row for row in rows if row['pid'] == target.pid and row['identity'][2] == rustc),None)
                    if observation:
                        identity = observation['identity']
                        repeated = json.loads(subprocess.check_output([helper,str(target.pid)+':'+str(identity[0])+':'+str(identity[1])],text=True,timeout=1))
                        assert observation in repeated and observation['parent'] == os.getpid() and observation['group'] == target.pid and observation['state'] == 'L'
                        target.send_signal(signal.SIGTERM)
                        break
                assert observation is not None
            stdout, stderr = target.communicate(timeout=3)
            result = {'mode':mode,'pid':target.pid,'parent_pid':os.getpid(),'command':command,'observation':observation,'rechecked':repeated,'wait_code':target.returncode,'elapsed_seconds':time.monotonic()-started,'stdout_bytes':len(stdout),'stderr_bytes':len(stderr),'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'source_bytes':len(source.encode()),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'output_present':(root/'output.rmeta').exists()}
            (root/'stdout.raw').write_bytes(stdout)
            (root/'stderr.raw').write_bytes(stderr)
            (root/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            assert target.returncode == (-15 if cancelling else 0)
            assert result['output_present'] is (not cancelling)
            print(mode,target.returncode,flush=True)
        finally:
            if target.poll() is None:
                target.kill()
                target.wait(timeout=2)


if __name__ == '__main__':
    run(Path(sys.argv[1]))
