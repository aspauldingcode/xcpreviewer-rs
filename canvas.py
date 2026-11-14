#!/usr/bin/env python3
"""Start Libre Canvas for the explicitly selected Swift source file."""
from pathlib import Path
import runpy
if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parent/'packages/canvas-dev/server.py'), run_name='__main__')
