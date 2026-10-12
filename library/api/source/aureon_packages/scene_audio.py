"""Fixed-rate audio view shared by AURS v2 behavior and its spectrum uniforms."""
import math
from audio.reactive import ReactiveAudioCore
from .expressions import AUDIO, AUDIO_V2


_DT=1./60.
_BAND_ATTACK=1.-math.exp(-_DT/.045)
_BAND_RELEASE=1.-math.exp(-_DT/.22)
_PEAK_DECAY=_DT*.45


def unit(value):
    try:
        value=float(value)
        return max(0.,min(1.,value)) if math.isfinite(value) else 0.
    except (ValueError,TypeError): return 0.


class SceneAudioContext:
    def __init__(self):
        self.core=ReactiveAudioCore(zone_count=8)
        self.phase=0
        self.bands=[0.]*32; self.peaks=[0.]*32; self.holds=[0.]*32
        self.audio={key:0. for key in AUDIO_V2}
        self.zones=(0.,)*8
        self.playing=False
        self.runtime={key:0. for key in ('playing','audio_mode','audio_active','reactive','paused','ambient')}
        # OPT 03: reuse temporary spectrum storage instead of allocating a shaped
        # list and 32 group slices on every behavior tick.  The arithmetic and
        # group boundaries intentionally remain identical to the pre-OPT path.
        self._shaped=[]

    def step(self,frame,enabled=True):
        audio_mode=bool(frame.audio_mode)
        paused=audio_mode and frame.playing is False
        active=bool(enabled and audio_mode and frame.playing is not False and frame.audio is not None)
        ambient=bool((not audio_mode) or (not enabled and not paused))
        self.playing=active
        runtime=self.runtime
        runtime.update(
            playing=1.0 if frame.playing is True else 0.0,
            audio_mode=1.0 if audio_mode else 0.0,
            audio_active=1.0 if active else 0.0,
            reactive=1.0 if enabled else 0.0,
            paused=1.0 if paused else 0.0,
            ambient=1.0 if ambient else 0.0,
        )
        # onset is a one-behaviour-tick pulse derived from the same shared core
        # event that legacy scenes observed through spark_seed changes.
        audio=self.audio
        audio['onset']=0.0
        audio['onset_strength']=0.0
        self.phase+=1
        core=self.core
        if self.phase%2==0:
            previous_seed=core.spark_seed
            core.ingest(frame.audio if active else None)
            core.tick()
            if active and core.spark_seed != previous_seed:
                audio['onset']=1.0
                audio['onset_strength']=unit(core.beat)

        # OPT 03: SceneAudioContext used to allocate an immutable
        # ReactiveSnapshot here although it only consumed the core immediately.
        # Read the same post-tick values directly; snapshot() remains available
        # to every other caller and its public contract is unchanged.
        self.zones=tuple(core.zones)
        values=core.value
        for name in core.CHANNELS:
            audio[name]=unit(values[name])
        audio['beat']=unit(core.beat)
        audio['fast']=unit(core.fast)
        audio['medium']=unit(core.medium)
        audio['slow']=unit(core.slow)
        audio['presence']=unit(core.presence)
        audio['phase']=unit(core.phase)
        for index in range(8):
            audio[f'zone{index}']=unit(self.zones[index])
        audio['flare']=unit(core.flare)
        audio['glint']=unit(core.glint_burst)

        frame_audio=frame.audio if active else None
        raw=getattr(frame_audio,'bands',()) if frame_audio is not None else ()
        if hasattr(raw,'__len__') and hasattr(raw,'__getitem__'):
            raw_count=min(512,len(raw))
        else:
            # Preserve the pre-OPT contract for uncommon iterable-only band
            # sources. Normal AudioAnalysisFrame bands are indexable, so this
            # compatibility fallback is not on the normal hot path.
            raw=tuple(raw)[:512]
            raw_count=len(raw)
        if raw_count:
            if len(self._shaped)!=raw_count:
                self._shaped=[0.]*raw_count
            shaped=self._shaped
            energy=unit(getattr(frame_audio,'normalized_energy',0.))
            scale=.52+.40*energy
            for index in range(raw_count):
                value=unit(raw[index])
                shaped[index]=min(.94,(.84*value**1.38+.16*value**.72)*scale)
        else:
            shaped=self._shaped
            if shaped:
                shaped.clear()
            raw_count=0

        bands=self.bands; peaks=self.peaks; holds=self.holds
        for i in range(32):
            if raw_count:
                left=i*raw_count//32
                right=max(left+1,(i+1)*raw_count//32)
                total=0.0
                for j in range(left,right):
                    total+=shaped[j]
                target=total/(right-left)
            else:
                target=0.0
            current=bands[i]
            coeff=_BAND_ATTACK if target>current else _BAND_RELEASE
            current+=(target-current)*coeff
            bands[i]=current
            if current>=peaks[i]:
                peaks[i]=current; holds[i]=.22
            else:
                hold=max(0.,holds[i]-_DT); holds[i]=hold
                if hold<=0.: peaks[i]=max(current,peaks[i]-_PEAK_DECAY)
