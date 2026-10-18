"""Pure proposal for bounded, spaced observation eligibility; never sleeps or touches UI."""
import math

def number(value):
 if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('finite time')
 return value

def decide(start,now,stop,cleanup_deadline,observed):
 """Fixed one-session offsets; callers retain history and execute only separately reviewed work."""
 start,now,stop,cleanup_deadline=map(number,(start,now,stop,cleanup_deadline))
 if not start<=now or not start<stop<cleanup_deadline or cleanup_deadline-stop<60:raise ValueError('time ordering/reserve')
 if type(observed) is not list or len(observed)>4:raise ValueError('observation history')
 offsets=(15,45,90,180)
 previous=start
 for i,t in enumerate(observed):
  t=number(t)
  if t<start+offsets[i] or t<previous or t>now or t>=stop:raise ValueError('history ordering/eligibility')
  previous=t
 if now>=stop or len(observed)==4:return {'decision':'cleanup','reason':'cutoff' if now>=stop else 'observation cap'}
 due=start+offsets[len(observed)]
 if due>=stop:return {'decision':'cleanup','reason':'next sample cannot fit'}
 if now<due:return {'decision':'independent_work','not_before':due}
 return {'decision':'sample_once','ordinal':len(observed)+1,'stop':stop}
