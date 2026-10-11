#!/usr/bin/env python3
"""Discover tools from an already running, enabled Xcode MCP service."""
import argparse
import json
from pathlib import Path
from reloop.core import atomic
from reloop.mcp_client import Client


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('research/build/xcode-mcp'))
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    client=None
    with (args.out/'bridge.stderr').open('wb') as stderr:
        try:
            client=Client(['xcrun','mcpbridge'],stderr,timeout=15)
            schema=client.request('tools/list',{})
            atomic(args.out/'tool-schema.json',schema)
            names=[t['name'] for t in schema.get('tools',[])]
            print(json.dumps({'tools':names,'preview_tools':[n for n in names if 'preview' in n.lower()]}))
            return 0
        except Exception as error:
            atomic(args.out/'result.json',{'available':False,'error':str(error),
                   'next':'Use an owned project in running Xcode with its MCP service enabled; inspect bridge.stderr.'})
            print(json.dumps({'available':False,'error':str(error)}));return 1
        finally:
            if client:client.close()


if __name__=='__main__':raise SystemExit(main())
