"""Explicit macOS birth/state retirement evidence; no path or absence inference."""
import json,pathlib,subprocess
class RetirementObserver:
    def __init__(self,binary):self.binary=str(pathlib.Path(binary).absolute())
    def snapshot(self,known):
        if type(known) is not dict or not 0<len(known)<=1024:raise ValueError('Bounded known lifetimes required')
        args=[]
        for pid,identity in sorted(known.items()):
            if (type(pid) is not int or not 0<pid<=2147483647 or type(identity) not in (tuple,list) or len(identity)!=3
                or any(type(x) is not int or not 0<=x<=18446744073709551615 for x in identity[:2])
                or type(identity[2]) is not str or not identity[2].startswith('/')):raise ValueError('Known lifetime identity required')
            args.append('%d:%d:%d' % (pid,*identity[:2]))
        result=subprocess.run([self.binary,*args],capture_output=True,check=True,timeout=2)
        if len(result.stdout)>1048576 or result.stderr:raise ValueError('Invalid retirement helper output')
        data=json.loads(result.stdout)
        if type(data) is not list or len(data)!=len(known):raise ValueError('Incomplete retirement result')
        rows={}
        for row in data:
            if type(row) is not dict or set(row)!={'pid','expected_birth','observed_birth','status'}:raise ValueError('Retirement row shape')
            pid=row['pid'];expected=row['expected_birth'];observed=row['observed_birth'];status=row['status']
            if type(pid) is not int or pid not in known or pid in rows or expected!=list(known[pid][:2]):raise ValueError('Retirement identity mismatch')
            if status not in ['live','retired','reused','unavailable']:raise ValueError('Retirement state')
            if status=='unavailable':
                if observed is not None:raise ValueError('Unavailable lifetime has no observed identity')
            elif (type(observed) is not list or len(observed)!=2 or any(type(x) is not int or x<0 for x in observed)
                or (status=='reused')==(observed==expected)):raise ValueError('Retirement birth/state mismatch')
            rows[pid]=row
        return rows
