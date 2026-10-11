#!/usr/bin/env python3
"""Decode owned plist bytes losslessly into tagged JSON; never invent XPC attachments."""
import argparse
import base64
import datetime
import json
import pathlib
import plistlib


def tagged(value):
    if isinstance(value,bytes):return {'$type':'data','base64':base64.b64encode(value).decode(),'bytes':len(value)}
    if isinstance(value,datetime.datetime):return {'$type':'date','value':value.isoformat()}
    if isinstance(value,plistlib.UID):return {'$type':'uid','value':value.data}
    if isinstance(value,dict):return {k:tagged(v) for k,v in value.items()}
    if isinstance(value,list):return [tagged(v) for v in value]
    return value


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path);a=p.parse_args()
    data=a.source.read_bytes()
    if len(data)>16*1024*1024:raise ValueError('plist exceeds 16 MiB analysis limit')
    result={'scope':'plist bytes only; not a model of XPC object attachments','value':tagged(plistlib.loads(data))}
    text=json.dumps(result,indent=2)+'\n'
    if a.out:a.out.write_text(text)
    else:print(text,end='')

if __name__=='__main__':main()
