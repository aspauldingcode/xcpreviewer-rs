from pathlib import Path
import subprocess,json,tempfile
artifact=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='owned-response-bridge-') as directory:
    work=Path(directory);binary=work/'native'
    build=subprocess.run(['xcrun','swiftc','-module-cache-path',str(work/'module-cache'),str(artifact/'native.swift'),'-o',str(binary)],capture_output=True,timeout=30)
    if build.returncode:print(build.stderr.decode())
    build.check_returncode()
    run=subprocess.run([str(binary)],capture_output=True,timeout=5)
    run.check_returncode();rows=json.loads(run.stdout)
    assert rows==json.loads((artifact/'native-results.json').read_text())
    print(json.dumps(rows,indent=2))
# Owned executable/cache removed; sealed evidence is unchanged by replay.
