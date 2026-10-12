"""64-band time-based dynamics; repeated cached audio frames are not new attacks."""
from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class SurfaceState:
    seconds: float
    bands: tuple
    energy: float
    treble: float
    waves: tuple
    orbit_phase: float = 0.

class SurfaceAudio:
    def __init__(self):self.reset()
    def reset(self):
        self.seconds=0.;self.orbit_phase=0.;self.bands=np.zeros(64);self.velocity=np.zeros(64)
        self.target=np.zeros(64);self.previous=np.zeros(64)
        self.last_stamp=None;self.energy=0.;self.treble=0.
        self.target_energy=0.;self.target_treble=0.
        self.waves=[];self.cooldown=0.;self.onsets=0;self.new_frames=0

    @staticmethod
    def _finite(value):
        try:return max(0.,min(1.,float(value))) if math.isfinite(float(value)) else 0.
        except (TypeError,ValueError,OverflowError):return 0.

    def advance(self,dt,frame):
        dt=max(0.,min(.1,float(dt)))
        stamp=getattr(frame,'time_ms',None) if frame is not None else None
        if frame is None:
            self.target.fill(0);self.previous.fill(0)
            self.target_energy=0.;self.target_treble=0.;self.last_stamp=None
        else:
            # A backward seek invalidates waves, previous bands and inertia.
            if stamp is not None and self.last_stamp is not None and stamp<self.last_stamp:
                self.reset()
            if stamp is None or stamp!=self.last_stamp:
                try:
                    raw=np.asarray(frame.bands,dtype=float).reshape(-1)
                    if not 2<=raw.size<=4096:raise ValueError('invalid bands')
                    raw=np.clip(np.nan_to_num(raw,nan=0.,posinf=0.,neginf=0.),0,1)
                    raw=np.interp(np.linspace(0,raw.size-1,64),np.arange(raw.size),raw)
                except (TypeError,ValueError,AttributeError):raw=np.zeros(64)
                rise=float(np.maximum(raw-self.previous,0).mean())
                bass_rise=float(np.maximum(raw[:16]-self.previous[:16],0).mean())
                strength=min(1.,rise*3.8+bass_rise*2.4)
                self.target_energy=self._finite(getattr(frame,'normalized_energy',0.))
                self.target_treble=self._finite(getattr(frame,'high',0.))
                if self.cooldown<=0 and strength>.10 and self.target_energy>.035:
                    # Position follows the strongest positive frequency change.
                    source=int(np.argmax(raw-self.previous))/63.*2-1
                    self.waves.append([0.,max(.2,strength),source*.9])
                    self.waves=self.waves[-8:];self.cooldown=.12;self.onsets+=1
                self.target[:]=raw/(.28+.72*raw)
                self.previous[:]=raw;self.last_stamp=stamp;self.new_frames+=1
        # Substeps keep the spring stable across timer stalls and 30/60 Hz.
        count=max(1,math.ceil(dt*240));step=dt/count
        for _ in range(count):
            self.velocity+=(self.target-self.bands)*215.*step
            self.velocity*=math.exp(-19.*step)
            self.bands+=self.velocity*step
            np.clip(self.bands,0,1.12,out=self.bands)
        self.energy+=(self.target_energy-self.energy)*(1-math.exp(-dt/.12))
        self.treble+=(self.target_treble-self.treble)*(1-math.exp(-dt/.065))
        self.seconds+=dt;self.cooldown=max(0.,self.cooldown-dt)
        # Integrate musical acceleration: changing energy cannot jump ring angles.
        self.orbit_phase+=dt*(.28*float(self.bands[:16].mean())+.18*self.energy)
        self.waves=[[age+dt,strength,x] for age,strength,x in self.waves if age+dt<1.25]
        return SurfaceState(self.seconds,tuple(self.bands),self.energy,self.treble,tuple(tuple(w) for w in self.waves),self.orbit_phase)
