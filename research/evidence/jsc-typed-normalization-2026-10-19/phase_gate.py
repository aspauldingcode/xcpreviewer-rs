"""C-source adapter around the pinned receipt validator; caller owns lock/pins/deadline."""
from pathlib import Path
from phase_prerequisites import require,digest,receipt

def dispatch(root,phase,launch):
 require(phase in ('compile','output-valid','fixture'),'Unknown phase')
 root=Path(root)
 if phase!='compile':
  source=digest(root/'probe.c');binary=digest(root/'probe')
  receipt(root,'compile',source,binary)
  if phase=='fixture':receipt(root,'output-valid',source,binary)
 return launch()
