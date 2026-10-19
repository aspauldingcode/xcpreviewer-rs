"""Consistency checks for transcribed sampled readiness, not raw AX proof."""
import math

def check(history):
 if type(history) is not list or not 1<=len(history)<=4:raise ValueError('history cap')
 offsets=[15,45,90,180]
 for i,value in enumerate(history):
  if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('sample type')
  due=max(offsets[i],(history[i-1] if i else 0)+(offsets[i]-(offsets[i-1] if i else 0)))
  if value<due:raise ValueError('sample spacing')
 return {'count':len(history),'scope':'Recorded consistency only; no native AX attestation'}
