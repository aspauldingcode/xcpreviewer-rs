"""Stateful owned-session observation permits; no UI or subprocess operations."""
import math
from readiness_schedule import decide
class Sampler:
 def __init__(self,start_wall,start_mono,stop_wall,cleanup_wall):
  for v in (start_wall,start_mono,stop_wall,cleanup_wall):
   if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('finite clock')
  decide(0,0,stop_wall-start_wall,cleanup_wall-start_wall,[])
  self._start_wall=start_wall;self._start_mono=start_mono;self._stop=stop_wall-start_wall;self._cleanup=cleanup_wall-start_wall;self._history=[];self._pending=None;self._failed=False;self._last=0;self._records=[]
 def _now(self,wall,mono):
  for v in (wall,mono):
   if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('finite clock')
  elapsed=mono-self._start_mono
  if elapsed<self._last or abs((wall-self._start_wall)-elapsed)>5:raise ValueError('clock divergence/regression')
  self._last=elapsed;return elapsed
 def issue(self,wall,mono):
  elapsed=self._now(wall,mono)
  if self._failed:return {'decision':'cleanup','reason':'recorded error'}
  if self._pending is not None:raise ValueError('pending sample must finish')
  result=decide(0,elapsed,self._stop,self._cleanup,self._history)
  if result['decision']=='sample_once':
   self._pending={'ordinal':result['ordinal'],'issued_elapsed':elapsed,'issued_wall':wall};self._records.append({'issue':dict(self._pending)})
   return {**result,'issued_wall':wall,'max_start_age_seconds':5}
  return result
 def complete(self,ordinal,outcome,wall,mono):
  elapsed=self._now(wall,mono)
  if type(ordinal) is not int or not self._pending or ordinal!=self._pending['ordinal'] or outcome not in ('ready','busy','error'):raise ValueError('completion binding')
  # This measures permit/completion timing; actual UI-call timing remains a caller obligation.
  if elapsed>=self._stop:raise ValueError('late completion')
  self._history.append(elapsed);self._records[-1]['completion']={'elapsed':elapsed,'wall':wall,'outcome':outcome};self._pending=None
  if outcome=='error':self._failed=True
  return {'completed':ordinal,'outcome':outcome}
 def snapshot(self):
  import copy
  return copy.deepcopy({'start_wall':self._start_wall,'start_mono':self._start_mono,'stop_elapsed':self._stop,'cleanup_elapsed':self._cleanup,'history':self._history,'pending':self._pending,'failed':self._failed,'records':self._records})
