"""Owned actual linker observation, cancellation and stress completion control."""
import json,subprocess,shutil,sys,re
from pathlib import Path
from reloop.core import ROOT,atomic,digest
from reloop.rustidentity import snapshot

def corpus(source,out):
    source=Path(source);out=Path(out);out.mkdir();cfg=json.loads((source/'config.json').read_text());prior=json.loads((source/'live/result.json').read_text());stage=source/'live'/prior['builds'][0]['stage']/'result'
    identity,pin=snapshot(cfg['rustc']);assert pin==cfg['toolchainPin'];host=next(s[6:] for s in identity['compiler_version'].splitlines() if s.startswith('host: '));linker=Path(cfg['rustc']).parent.parent/'lib/rustlib'/host/'bin/rust-lld';assert digest(linker)==identity['linkers']['rust-lld']['sha256']
    contract=out/'contract.rs';shutil.copyfile(ROOT/'tools/re/rust/canvas-core/src/contract.rs',contract);assert digest(contract)==prior['builds'][0]['receipt']['sources']['contract.rs'];text=(stage/'module.rs').read_text();text=re.sub(r'#\[path = "[^"]+"\]', '#[path = "'+str(contract)+'"]',text);(out/'kernel.rs').write_text(text)
    config={**cfg,'linker':str(linker),'linkerSha':digest(linker),'generated':str(out/'kernel.rs'),'source':str(Path(cfg['input'])/'0-source.swift'),'expected':str(Path(cfg['input'])/'0-expected.raw'),'module':str(stage/'view.wasm'),'config':prior['builds'][0]['receipt']['config']};atomic(out/'config.json',config)
    r=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/rust_linker_control.js'),str(out/'config.json'),str(out/'controls')],capture_output=True,timeout=20);(out/'control.stdout').write_bytes(r.stdout);(out/'control.stderr').write_bytes(r.stderr);r.check_returncode();assert snapshot(cfg['rustc'])[1]==pin and digest(linker)==config['linkerSha']
    d=json.loads((out/'controls/result.json').read_text());facts={'rust_linker_observed_cases':len(d['controls']),'rust_linker_abort_drained':d['controls'][0]['execution']['report']['drained'] and d['controls'][0]['execution']['report']['failure']=='abort','rust_linker_complete_bytes':16384,'rust_linker_zero_workers':d['status']['liveWorkers']==0};atomic(out/'observations.json',{'observations':facts,'scope':d['scope']});return facts
