"""Trusted controller for package-defined expressions and a fragment shader."""
import math
import time
from audio.reactive import ReactiveAudioCore
from .expressions import AUDIO


class PackageSceneRuntime:
    def __init__(self, definition, quality, reactive):
        self.definition = definition
        self.quality = quality if quality in definition.quality else ('high' if quality == 'extreme' else 'medium')
        self.reactive = bool(reactive)
        self.scene = self  # Existing Info panel reads scene.quality.
        self.core = ReactiveAudioCore(zone_count=8)
        self.elapsed = 0.0
        self.values = {}
        self.zones = (0.0,)*8
        self.signals = {name:(b if kind=='integrator' else 0.)
                        for name,kind,expr,a,b in definition.signals}
        lines = definition.source.splitlines(keepends=True)
        # Keep #version first; quality constants are owned by the validated descriptor.
        insertion = next(i for i,line in enumerate(lines) if line.lstrip().startswith('#version'))+1
        quality_index={'low':0,'medium':1,'high':2,'extreme':3}[self.quality]
        defines = f'#define AUR_QUALITY_TIER {quality_index}\n#define AUR_QUALITY_LEVEL {float(quality_index):.1f}\n' + ''.join(f'#define {name} {value}\n' for name,value in definition.quality[self.quality].items())
        lines.insert(insertion, '\n'+defines)
        self.shader_source = ''.join(lines)

    def update(self, dt, frame):
        started=time.perf_counter_ns()
        dt = max(0.,min(.1,float(dt)))
        self.elapsed += dt
        active = self.reactive and frame.audio_mode and frame.playing is not False
        if active:
            self.core.ingest(frame.audio)
            self.core.tick()
        else:
            self.core.reset()
        snapshot = self.core.snapshot()
        audio = {}
        zones = tuple(snapshot.zones[:8]) if active else (0.,)*8
        for name in AUDIO:
            if name.startswith('zone') and name[4:].isdigit():
                index = int(name[4:])
                value = float(zones[index]) if 0 <= index < len(zones) else 0.
            else:
                value = float(getattr(snapshot,name,0.)) if active else 0.
            audio[name] = value if math.isfinite(value) else 0.
        context={'time':self.elapsed,'dt':dt,'pi':math.pi,'audio':audio,'signal':self.signals}
        for name,kind,expr,a,b in self.definition.signals:
            value=expr.value(context)
            if kind=='integrator': value=(self.signals[name]+value*dt)%a
            elif kind=='envelope':
                current=self.signals[name]
                value=current+(value-current)*(1-math.exp(-dt/(a if value>current else b)))
            self.signals[name]=value
        behavior_done=time.perf_counter_ns()
        self.values={'u_time':self.elapsed, **{'u_audio_'+k:v for k,v in audio.items()}}
        for name,(kind,expressions) in self.definition.uniforms.items():
            values=tuple(e.value(context) for e in expressions)
            self.values[name]=values[0] if kind=='float' else values
        self.zones=zones
        publish_done=time.perf_counter_ns()
        self._perf_behavior_ms=(behavior_done-started)/1_000_000.0
        self._perf_uniform_prep_ms=(publish_done-behavior_done)/1_000_000.0

    def performance_timings(self):
        return {
            'cpu_behavior': getattr(self,'_perf_behavior_ms',None),
            'uniform_prep': getattr(self,'_perf_uniform_prep_ms',None),
        }

    def uniforms(self):
        return self.values,self.zones
