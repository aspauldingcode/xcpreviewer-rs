#!/usr/bin/env python3
"""Fresh-verify an explicitly anchored completed research run without rerunning producers."""
import argparse
import json
from reloop.core import Controller
from reloop.graphloop import adopt_verified

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task',required=True)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--anchor',required=True)
    args=parser.parse_args()
    report=adopt_verified(Controller(),args.task,args.run_id,args.anchor)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
