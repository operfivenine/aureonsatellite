"""Volcanic valley: isolated continuous travel and frequency-specific envelopes."""
import math
from audio.reactive import ReactiveAudioCore
from .quality import QUALITY, CHANNELS


class VolcanicValleyGL:
    def __init__(self, quality="medium", reactive=False):
        self.quality = quality if quality in QUALITY else "medium"
        self.reactive = bool(reactive)
        self.core = ReactiveAudioCore()
        self.seconds = self._accumulator = 0.0
        self._playing = self._audio_mode = None
        self._bass = self._mid = self._high = 0.0
        self._travel = self._lava_flow = self._smoke_flow = 0.0
        self._smoke_phase = 0.0
        self._previous_low = self._previous_high = 0.0
        self._heat_events = [[9.0,0.0,0.0,0.0] for _ in range(8)]
        self._ember_events = [[9.0,0.0,0.0,0.0] for _ in range(4)]
        self._event_serial = 0

    def set_transport(self, playing=None, audio_mode=None):
        self._playing, self._audio_mode = playing, audio_mode

    @staticmethod
    def _smooth(value, target, attack, release, dt):
        return value+(target-value)*(1.0-math.exp(-dt/(attack if target>value else release)))

    def advance(self, dt, frame):
        dt=max(0.0,min(.1,float(dt)))
        self.seconds+=dt
        paused=self._audio_mode is True and self._playing is False
        self._accumulator+=dt
        while self._accumulator>=1/30:
            for event in self._heat_events+self._ember_events:
                event[0]=min(9.0,event[0]+1/30)
            self.core.ingest(frame if self.reactive and not paused else None)
            self.core.tick()
            s=self.core.snapshot()
            if paused:
                bass=mid=high=0.0
            elif not self.reactive or self._audio_mode is False:
                bass=.10+.06*math.sin(self.seconds*.65)
                mid,high=.12,.08
            else:
                # A bass envelope plus its positive transient, not global beat
                # (which would make treble-only hits pulse the lava).
                bass=min(1.0,.80*s.low+.35*max(0.0,s.low-self._bass))
                mid=s.mid
                high=s.high*(.20+.80*max(s.flux,s.fast))
            self._bass=self._smooth(self._bass,bass,.075,.50,1/30)
            self._mid=self._smooth(self._mid,mid,.16,.70,1/30)
            self._high=self._smooth(self._high,high,.035,.18,1/30)
            # Scene-local, independent frequency onsets. Never repurpose global beat.
            active=self.reactive and not paused and self._audio_mode is not False and frame is not None
            low_raw=self.core.clamp(getattr(frame,"low",0.0)) if active else 0.0
            high_raw=self.core.clamp(getattr(frame,"high",0.0)) if active else 0.0
            for events,raw,previous,lifetime,ahead,gap,threshold in (
                (self._heat_events,low_raw,self._previous_low,1.35,9.0,.14,.022),
                (self._ember_events,high_raw,self._previous_high,.65,4.0,.10,.018)):
                rise=max(0.0,raw-previous)
                # Reuse only expired slots: rapid hats cannot teleport live embers.
                slot=max(events,key=lambda event:event[0])
                if active and raw>.10 and rise>threshold and slot[0]>=lifetime and min(e[0] for e in events)>=gap:
                    self._event_serial=(self._event_serial+1)%4096
                    slot[:]=[0.0,min(1.0,.30+rise*2.1+raw*.30),
                             (self._travel+ahead)%256.0,float(self._event_serial)]
            self._previous_low,self._previous_high=low_raw,high_raw
            self._accumulator-=1/30
        # Terrain and all world-space lattices repeat in Z at exactly 256 units.
        self._travel=(self._travel+dt*(.12 if paused else .36)) % 256.0
        self._lava_flow=(self._lava_flow+dt*(.18+.10*self._bass)) % 32.0
        self._smoke_flow=(self._smoke_flow+dt*.32) % 32.0
        self._smoke_phase=(self._smoke_phase+dt*(.9+2.5*self._mid)) % math.tau

    def uniforms(self):
        s=self.core.snapshot()
        v={"u_"+key:max(0.0,min(1.0,float(getattr(s,key)))) for key in CHANNELS}
        v.update(u_time=(self.seconds%7200)*math.tau/7200,
                 u_travel=self._travel,u_lava_flow=self._lava_flow,u_smoke_flow=self._smoke_flow,
                 u_lava_pulse=self._bass,u_smoke_light=self._mid,u_ember_drive=self._high)
        v["u_smoke_phase"]=self._smoke_phase
        for prefix,events in (("heat",self._heat_events),("burst",self._ember_events)):
            for i,event in enumerate(events):
                for field,value in zip(("age","strength","z","seed"),event):
                    v[f"u_{prefix}{i}_{field}"]=value
        return v,tuple(max(0.0,min(1.0,float(z))) for z in s.zones)
