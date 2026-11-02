from pathlib import Path
import fcntl,time
p=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);(p/'lease2-ready').touch();end=time.monotonic()+180
 while time.monotonic()<end and not (p/'lease2-stop').exists():time.sleep(.1)
 (p/'lease2-released').touch()
