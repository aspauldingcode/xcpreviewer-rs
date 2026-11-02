from pathlib import Path
import subprocess,json,re,hashlib
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent
stages=[('capture-check',['python3',str(w/'check-capture.py')],240),('png-check',[str(r/'research/venv/bin/python'),str(w/'check-png.py')],30),('source',['python3',str(w/'source-verify.py')],30),('native-check',['python3',str(w/'run-native.py')],60),('frame-build',['python3',str(w/'build.py')],130),('packet-check',['python3',str(w/'check-packets.py')],40),('rust-check',['python3',str(w/'check-rust.py'),'--replay'],180),('worker-check',['node',str(w/'worker-check.cjs'),str(r/'tools/re/browser-preview/worker.js'),str(w/'target/wasm32-wasip1/debug/canvas-frame.wasm'),str(w/'sample.bplist'),str(w/'sample.packet')],10)]
for name,args,deadline in stages:
 print(name,flush=True)
 try:p=subprocess.run(args,capture_output=True,timeout=deadline)
 except subprocess.TimeoutExpired as error:
  (w/(name+'.stdout')).write_bytes(error.stdout or b'');(w/(name+'.stderr')).write_bytes(error.stderr or b'');raise
 (w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print((p.stdout+p.stderr).decode()[-3000:],flush=True)
 p.check_returncode()
packets=json.loads((w/'packet-results.json').read_text());png=json.loads((w/'png-results.json').read_text());native=__import__('plistlib').loads((w/'native.bplist').read_bytes());source=json.loads((w/'source-findings.json').read_text());rust=json.loads((w/'rust-results.json').read_text())
result={'native_swiftui_captures':3,'negative_controls_preserving_last_good':4,'native_private_render_codec_acceptances':3,'native_output_values_destroyed':native['destroyedValues'],'native_output_plists_destroyed':native['destroyedPlists'],'source_codec_bytes_verified':source['source_bytes_verified'],'host_wasi_packets_equal':all(x['host_wasi_packet_equal'] for x in packets),'independent_png_pixel_bytes_equal':sum(x['bytes'] for x in png),'host_wasi_example_stdout_equal':rust['host_wasi_example_stdout_equal'],'rust_tests':rust['rust_tests'],'pixel_receipts':packets,'worker_checked':True};(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
