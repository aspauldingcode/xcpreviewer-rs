#!/bin/sh
# Installs only free Python tooling in this repository's ignored environment.
set -eu
project=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$project"
python3 -m venv research/venv
research/venv/bin/python -m pip install --cache-dir research/build/pip-cache -r research/loop/requirements.lock
research/venv/bin/python tools/re/agent.py doctor
