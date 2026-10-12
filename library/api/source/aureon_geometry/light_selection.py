"""Bounded temporal light slots. Opt-in mesh extension; no extra render pass."""
from dataclasses import dataclass
from collections import deque

FEATURE='scene.mesh_light_selection.experimental.v1'

def compile_lighting(raw,features):
    from aureon_packages.schema import obj,number
    from aureon_packages.expressions import PackageError
    if raw is None:return None
    if FEATURE not in features:raise PackageError('Smooth mesh lighting requires '+FEATURE)
    obj(raw,('quality','fade_seconds','hysteresis'),('quality','fade_seconds','hysteresis'))
    number(raw['fade_seconds'],.15,2);number(raw['hysteresis'],.05,.75)
    obj(raw['quality'],('low','medium','high'),('low','medium','high'))
    previous=0
    for name,limit in (('low',1),('medium',2),('high',4)):
        q=obj(raw['quality'][name],('sources','reach'),('sources','reach'))
        if type(q['sources']) is not int or not 1<=q['sources']<=limit or q['sources']<previous:raise PackageError('Invalid quality light budget')
        number(q['reach'],20,400);previous=q['sources']
    if not raw['quality']['low']['reach']<=raw['quality']['medium']['reach']<=raw['quality']['high']['reach']:raise PackageError('Light reach must increase with quality')
    return raw

@dataclass
class Slot:
    source:int|None=None
    weight:float=0.
    retiring:bool=False

class LightSlots:
    def __init__(self,config,quality):
        self.config=config;self.budget=config['quality'][quality]['sources'];self.reach=config['quality'][quality]['reach']
        self.reset()
    def reset(self):
        self.slots=[Slot() for _ in range(self.budget)];self.clock=None;self.switches=0;self.replacements=deque(maxlen=32)
    def select(self,scores,clock):
        # State advances once per scene clock, independent of resize/repaint rate.
        initial=self.clock is None
        dt=0 if initial else max(0,min(.1,clock-self.clock));self.clock=clock
        incumbents={s.source for s in self.slots if s.source is not None and not s.retiring}
        hysteresis=self.config['hysteresis']
        ranked=sorted(scores,key=lambda i:(-scores[i]*(1+hysteresis if i in incumbents else 1),i))
        wanted=set(ranked[:self.budget]);step=dt/self.config['fade_seconds']
        if initial:
            for slot,i in zip(self.slots,ranked):slot.source=i;slot.weight=1
        for slot in self.slots:
            if slot.source is None:continue
            if slot.source not in wanted:slot.retiring=True
            # Once retirement begins it completes: nearby ties cannot reverse
            # a half-faded slot repeatedly and starve the incoming source.
            slot.weight=max(0,slot.weight-step) if slot.retiring else min(1,slot.weight+step)
            if slot.retiring and slot.weight<=1e-8:
                self.replacements.append((slot.source,slot.weight));slot.source=None;slot.weight=0;slot.retiring=False;self.switches+=1
        occupied={s.source for s in self.slots if s.source is not None}
        missing=[i for i in ranked[:self.budget] if i not in occupied]
        for slot in self.slots:
            if slot.source is None and missing:slot.source=missing.pop(0);slot.weight=0;slot.retiring=False
        # Smoothstep makes both endpoints have zero slope. Identity can change
        # only at zero intensity and the number of GPU slots never exceeds budget.
        return [(s.source,s.weight*s.weight*(3-2*s.weight)) for s in self.slots]
