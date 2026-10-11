#!/usr/bin/env python3
"""Inspect or execute the explicitly bounded live-swap research graph."""
import argparse
import json
from reloop.core import Controller
import reloop.graphloop as graphloop


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--resume')
    args = parser.parse_args()
    graphloop.DEFAULT_CONFIG = 'research/loop/live-swap-runner.json'
    controller = Controller()
    result = graphloop.run(controller, args.resume) if args.execute else graphloop.inspect(controller)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
