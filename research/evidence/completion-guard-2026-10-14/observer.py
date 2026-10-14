#!/Users/8amps/xcpreviewer-rs/research/venv/bin/python
import hashlib
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT/'research/build/libproc-observer-aa9cd15f087d41ad8f7bbe00c4162499/owned-process-snapshot'
assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == '718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
time.sleep(0.2)
os.execv(str(HELPER),[str(HELPER),*sys.argv[1:]])
