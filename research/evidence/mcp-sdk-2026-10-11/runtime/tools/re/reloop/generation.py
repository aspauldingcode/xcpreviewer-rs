"""Owned reconstruction policy, not recovered Canvas sequencing."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Ticket:
    epoch:int
    generation:int
    serial:int

class Gate:
    def __init__(self):
        self.epoch=0;self.generation=0;self.serial=0;self.current=None;self.expected=None;self.frame=None
    def admit(self,generation,pixels):
        if type(generation) is not int or not self.generation<generation<2**64:raise ValueError('Nonmonotonic generation')
        if type(pixels) is not bytes or not 0<len(pixels)<=1048576:raise ValueError('Invalid immutable frame')
        self.generation=generation;self.serial+=1;self.current=Ticket(self.epoch,generation,self.serial);self.expected=pixels
        return self.current
    def commit(self,ticket,pixels):
        if type(ticket) is not Ticket or self.current is None or ticket!=self.current or type(pixels) is not bytes or pixels!=self.expected:return False
        self.frame=pixels;self.current=None;self.expected=None;return True
    def cancel(self,ticket):
        if self.current is not None and ticket==self.current:self.current=None;self.expected=None
    def reset(self):
        self.epoch+=1;self.generation=0;self.current=None;self.expected=None


def controls(first,second,delayed,mode):
    # Explicit expected truth table, independent of Gate control flow.
    expectations={'current':True,'superseded':False,'duplicate':False,'cancelled':False,'reset':False,'wrong-payload':False,'frozen-first':True,'delayed-first':mode=='separate'}
    results={}
    g=Gate();t=g.admit(2,second);results['current']=g.commit(t,second);results['duplicate']=g.commit(t,second)
    g=Gate();old=g.admit(1,first);g.admit(2,second);results['superseded']=g.commit(old,first)
    g=Gate();t=g.admit(2,second);g.cancel(t);results['cancelled']=g.commit(t,second)
    g=Gate();t=g.admit(1,first);g.reset();g.admit(1,first);results['reset']=g.commit(t,first)
    g=Gate();t=g.admit(2,second);results['wrong-payload']=g.commit(t,first)
    g=Gate();t=g.admit(1,first);results['frozen-first']=g.commit(t,first)
    g=Gate();t=g.admit(1,first);results['delayed-first']=g.commit(t,delayed)
    return {'passed':results==expectations,'expected':expectations,'actual':results,'controls':len(results)}


def corpus(out):
    import json,pathlib
    from reloop.surfacereuse import corpus as native
    from reloop.core import atomic
    out=pathlib.Path(out);source=out/'native';source.mkdir()
    facts=native(source)
    if facts.get('verified_reuse_cases')!=8 or facts.get('helper_failures')!=0:raise ValueError('Native reuse corpus failed')
    rows=[]
    for folder in sorted(p for p in source.iterdir() if p.is_dir()):
        mode=json.loads((folder/'stdout.json').read_text())['mode']
        first=(folder/'producer-first.bin').read_bytes();second=(folder/'producer-next.bin').read_bytes();delayed=(folder/'delayed-first.bin').read_bytes()
        if first==second:raise ValueError('Missing positive content change')
        rows.append({'case':folder.name,**controls(first,second,delayed,mode)})
    atomic(out/'generation-controls.json',{'cases':rows,'native':facts})
    return {'verified_executions':sum(r['passed'] for r in rows),'controls':sum(r['controls'] for r in rows),'native':facts,
            'scope':'Owned native mutable/separate CPU frames feed explicit immutable-content and session/generation commit policy. Proposed reconstruction policy; no actual Canvas sequencing, races, fences or kernel reclamation.'}
