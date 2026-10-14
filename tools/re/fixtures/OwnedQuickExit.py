import os
import sys
from pathlib import Path

payload = bytes([0,1,2,255,10,42,99,128])
Path(sys.argv[1],'owned.raw').write_bytes(payload)
os.write(1,payload)
os._exit(0)
