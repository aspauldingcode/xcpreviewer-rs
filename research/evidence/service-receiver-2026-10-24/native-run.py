from pathlib import Path
import subprocess,json,tempfile
artifact=Path(__file__).parent
r=Path('/Users/8amps/xcpreviewer-rs')
with tempfile.TemporaryDirectory(prefix='owned-service-receiver-') as directory:
    binary=Path(directory)/'native'
    build=subprocess.run(['xcrun','clang','-fblocks','-Wall','-Wextra','-Werror',str(artifact/'native.c'),'-o',str(binary)],capture_output=True,timeout=30)
    if build.returncode: print(build.stderr.decode())
    build.check_returncode()
    run=subprocess.run([str(binary),str(r/'tools/re/rust/canvas-core/tests/fixtures/service-property-list/nested.wire-data')],capture_output=True,timeout=5)
    if run.stderr: print(run.stderr.decode())
    run.check_returncode()
    result=json.loads(run.stdout)
    assert result=={'plain_reply':False,'one_way_reply':0,'request_reply':1,'reply_callback_accepted':1,'wire_bytes_equal':1,'wire_length':301,'errors_before_cleanup':0,'timed_out':False}
    print(json.dumps(result,indent=2))
# This replay leaves sealed evidence unchanged and removes its owned binary.
