"""Read-only analyzer adapter. No decoding, playback controls, or profile writes."""
from dataclasses import dataclass, asdict
import math, time

def bounded(value):
    try:
        value=float(value)
        return max(0., min(1., value)) if math.isfinite(value) else 0.
    except (TypeError, ValueError):
        return 0.

@dataclass(frozen=True)
class AudioSignals:
    rms: float=0.
    energy: float=0.
    low: float=0.
    mid: float=0.
    high: float=0.
    beat: float=0.

def analyzer_signals(frame):
    return AudioSignals(**{name:bounded(getattr(frame, field, 0.)) for name,field in
        (('rms','rms'),('energy','normalized_energy'),('low','low'),('mid','mid'),('high','high'),('beat','beat'))})

def player_packet(player):
    # Called on the player's GUI thread. Copy scalar values only.
    if player.player.playbackState().name != 'PlayingState':
        return asdict(AudioSignals())
    return asdict(analyzer_signals(player.surface._current_audio_frame()))

class AudioBridge:
    def __init__(self):
        self.values=AudioSignals();self.target=AudioSignals();self.received=-1e6
        self.demo=False;self.enabled=True;self._previous_low=0.
        self.attack_rate=16.;self.release_rate=5.
        self.packets=0;self.peak_input={name:0. for name in AudioSignals.__dataclass_fields__}

    def receive(self, packet):
        self.target=AudioSignals(**{name:bounded(packet.get(name,0.)) for name in AudioSignals.__dataclass_fields__})
        self.received=time.monotonic()
        self.packets+=1
        for name in self.peak_input:self.peak_input[name]=max(self.peak_input[name],getattr(self.target,name))

    def update(self, dt, elapsed):
        target=self.target if time.monotonic()-self.received < .65 else AudioSignals()
        if self.demo:
            pulse=max(0.,math.sin(elapsed*math.tau*1.9))**8
            target=AudioSignals(.12+.35*pulse,.15+.7*pulse,.18+.8*pulse,.3+.3*math.sin(elapsed)**2,.12+.65*pulse,pulse)
        if not self.enabled:target=AudioSignals()
        values={}
        for name in AudioSignals.__dataclass_fields__:
            old=getattr(self.values,name);new=getattr(target,name)
            speed=self.attack_rate if new>old else self.release_rate
            values[name]=old+(new-old)*(1.-math.exp(-dt*speed))
        # Optional onset estimate lives entirely in the Lab, never in Aureon's analyzer.
        onset=max(0.,target.low-self._previous_low-.075)*2.2
        self._previous_low=target.low
        values['beat']=max(values['beat'],bounded(onset))
        self.values=AudioSignals(**values)
        return self.values
