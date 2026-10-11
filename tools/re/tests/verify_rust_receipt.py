"""Independent receipt expectations and fresh frozen-validator replay."""
import hashlib,json,subprocess,shutil,importlib.util,re
from pathlib import Path
FIELDS={'source_sha256','module_sha256','config','rustc_sha256','toolchain_sha256','sources','generated_sha256','cache_hit','target','scope'}
PINS=['source_sha256','module_sha256','rustc_sha256','toolchain_sha256','generated_sha256']
def valid(r,context):
    if type(r) is not dict or set(r)!=FIELDS:return False
    if any(type(r[k]) is not str or re.fullmatch('[a-f0-9]{64}',r[k]) is None or r[k]!=context[k] for k in PINS):return False
    c=r['config']
    if type(c) is not dict or set(c)!={'width','height','alphas','reverse'}:return False
    if any(type(c[k]) is not int or not 1<=c[k]<=64 for k in ['width','height']):return False
    if type(c['alphas']) is not list or len(c['alphas'])!=3 or any(type(x) is not int or not 0<=x<=8 for x in c['alphas']):return False
    if type(c['reverse']) is not int or c['reverse'] not in [0,1]:return False
    if type(r['sources']) is not dict or set(r['sources'])!={'contract.rs','wasm-template.rs'} or r['sources']!=context['sources']:return False
    if any(type(v) is not str or re.fullmatch('[a-f0-9]{64}',v) is None for v in r['sources'].values()):return False
    return r['cache_hit'] is False and r['target']=='wasm32-wasip1' and r['scope']=='Finite primary literal expression lowering; not general Swift compilation'
def verify(folder):
    folder=Path(folder);s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader);reader.verify(folder)
    source=json.loads((folder/'control/live/result.json').read_text());d=json.loads((folder/'gate/result.json').read_text());assert len(d['valid'])==3 and len(d['mutants'])==34
    contexts=[]
    for row,build in zip(d['valid'],source['builds']):
        expected={k:build['receipt'][k] for k in PINS};expected['sources']=build['receipt']['sources'];assert row['receipt']==build['receipt'] and row['context']==expected and valid(row['receipt'],expected);contexts.append(expected)
    names=[x['case'] for x in d['mutants']];assert len(set(names))==34 and 'reverse-boolean' in names
    for row in d['mutants']:assert row['context']==contexts[0] and type(row['error']) is str and row['error'] and not valid(row['receipt'],contexts[0])
    script="const fs=require('fs'),a=require('assert/strict'),v=require(process.argv[1]).validateRustReceipt,d=JSON.parse(fs.readFileSync(process.argv[2]));for(const r of d.valid)v(r.receipt,r.context);for(const r of d.mutants)a.throws(()=>v(r.receipt,r.context));"
    r=subprocess.run([shutil.which('node'),'-e',script,str((folder/'reader/rust_receipt.js').resolve()),str((folder/'gate/result.json').resolve())],capture_output=True,timeout=5);assert r.returncode==0,r.stderr.decode();return {'valid':3,'mutants':34,'bytes':49152,'review':'pending'}
