import os
import sys
import time
from pathlib import Path

mode = sys.argv[1]
root = Path(sys.argv[2])
assert mode in ['delayed-zero','delayed-failure','late','abort']
os.alarm(3)
if mode == 'late': time.sleep(1.2)
payload = bytes([0,1,2,255,10,42,99,128])
(root/'owned.raw').write_bytes(payload)
os.write(1,payload)
os._exit(43 if mode == 'delayed-failure' else 0)
