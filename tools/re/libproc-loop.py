#!/usr/bin/env python3
"""Run a bounded reviewed graph round with explicit public libproc observation.

Requires the executable graph runner integration. Default ps behavior remains
available; backend selection is fixed for every owned tree in this controller.
"""
import argparse
import json
import uuid
from reloop.core import Controller, identity, load
import reloop.core as core
from reloop.libprocobserver import build


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='research/loop/observer-runner.json')
    parser.add_argument('--resume')
    parser.add_argument('--only',help='Standalone bounded campaign selection; graph integration optional')
    args=parser.parse_args()
    # Compile only while the controller resource is exclusively held. Use a
    # private helper path so another later run cannot replace this binary.
    with Controller().lock():
        observer,receipt=build('research/build/libproc-observer-'+uuid.uuid4().hex)
    if args.only:
        original=core.identity
        core.identity=lambda:{**identity(),'owned_process_observer':receipt}
        try:
            result=Controller(process_observer=observer.snapshot).session(load('research/loop/campaign.json'),max_experiments=1,minutes=3,max_mb=32,only=args.only)
            print(json.dumps(result,indent=2))
        finally:core.identity=original
        return
    import reloop.graphloop as graphloop
    graphloop.DEFAULT_CONFIG=args.config
    original=graphloop.identity
    graphloop.identity=lambda:{**identity(),'owned_process_observer':receipt}
    try:
        wake=graphloop.run(Controller(process_observer=observer.snapshot),resume=args.resume)
        print(json.dumps({'id':wake['id'],'state':wake['state'],
                         'rounds':[{k:r.get(k) for k in ('task','run_id','state','execution','verdict','verification')} for r in wake['rounds']]},indent=2))
    finally:
        graphloop.identity=original

if __name__=='__main__':main()
